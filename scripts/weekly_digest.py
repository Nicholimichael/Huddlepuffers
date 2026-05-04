"""
weekly_digest.py — Compares the latest two ranking snapshots and emits a
Markdown digest of what changed for the Huddlepuffers dynasty league.

Designed to be invoked by the Cowork scheduled task each Wednesday morning.

Inputs:
  - data/snapshots/rankings_YYYY-MM-DD.json  (created by refresh_platform.sh)
  - db/fantasy.sqlite (for transactions and current rosters)

Outputs:
  - reports/weekly_digest_YYYY-MM-DD.md  (the Markdown digest)
  - returns the digest path on stdout (last line)
"""

from __future__ import annotations
import json
import sqlite3
import sys
import datetime as dt
from pathlib import Path

# Make project-root config importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

PROJECT = config.PROJECT_ROOT
SNAPSHOTS = config.SNAPSHOTS_DIR
REPORTS = config.REPORTS_DIR
DB = config.DB_PATH
ME_DEFAULT = config.MY_USER_ID  # overridden by snapshot meta if present


def latest_two_snapshots() -> tuple[Path | None, Path | None]:
    snaps = sorted(SNAPSHOTS.glob("rankings_*.json"))
    if len(snaps) == 0:
        return None, None
    if len(snaps) == 1:
        return snaps[0], None
    return snaps[-1], snaps[-2]


def load_snap(p: Path) -> dict:
    with open(p) as f:
        return json.load(f)


def index_players(snap: dict) -> dict[str, dict]:
    return {p["player_id"]: p for p in snap.get("players", []) if p.get("player_id")}


def fmt_delta(v: float | None, sign: bool = True) -> str:
    if v is None:
        return ""
    s = "+" if v >= 0 and sign else ""
    return f"{s}{v:.1f}"


def transactions_since(conn: sqlite3.Connection, since: dt.date) -> list[dict]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT type, status, created, settings
        FROM transactions
        WHERE created/1000 >= ?
        ORDER BY created DESC
        LIMIT 200
        """,
        (int(dt.datetime.combine(since, dt.time.min).timestamp()),),
    )
    return [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]


def write_digest(prev: dict, curr: dict, me: str) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    today = dt.date.today()
    out = REPORTS / f"weekly_digest_{today.isoformat()}.md"

    p_idx = index_players(prev) if prev else {}
    c_idx = index_players(curr)

    # Movers: by dynasty_score change
    movers = []
    for pid, c in c_idx.items():
        p = p_idx.get(pid)
        if not p:
            continue
        ds_d = (c.get("dynasty_score") or 0) - (p.get("dynasty_score") or 0)
        ws_d = (c.get("winnow_score") or 0) - (p.get("winnow_score") or 0)
        rk_d = (p.get("dynasty_overall_rank") or 999) - (c.get("dynasty_overall_rank") or 999)
        # rk_d is positive when rank improved (lower number)
        movers.append({
            "p": c, "ds_d": ds_d, "ws_d": ws_d, "rk_d": rk_d,
        })

    risers = sorted(movers, key=lambda m: -m["ds_d"])[:10]
    fallers = sorted(movers, key=lambda m: m["ds_d"])[:10]

    # New rookies / additions
    new_ids = set(c_idx) - set(p_idx)
    new_players = sorted(
        [c_idx[i] for i in new_ids],
        key=lambda p: -(p.get("dynasty_score") or 0)
    )[:8]

    # My team movement
    my_now = [p for p in c_idx.values() if p.get("owner_id") == me]
    my_movers = []
    for p in my_now:
        prev_p = p_idx.get(p["player_id"])
        if not prev_p:
            continue
        d = (p.get("dynasty_score") or 0) - (prev_p.get("dynasty_score") or 0)
        if abs(d) >= 1.0:
            my_movers.append((p, d))
    my_movers.sort(key=lambda x: -x[1])

    # Transactions
    txns = []
    if DB.exists():
        try:
            conn = sqlite3.connect(DB)
            txns = transactions_since(conn, today - dt.timedelta(days=7))
            conn.close()
        except Exception:
            pass

    # ---- write ----
    lines = []
    lines.append(f"# Huddlepuffers Weekly Digest — {today.isoformat()}")
    lines.append("")
    if not prev:
        lines.append("> First snapshot run — no week-over-week comparison yet. "
                     "Next week's digest will show what changed.")
        lines.append("")
    else:
        prev_date = prev.get("meta", {}).get("generated_at", "previous snapshot")
        lines.append(f"_Comparing **{today.isoformat()}** to **{prev_date[:10]}**._")
        lines.append("")

    # League activity
    lines.append("## League activity (last 7 days)")
    if txns:
        by_type: dict[str, int] = {}
        for t in txns:
            by_type[t["type"]] = by_type.get(t["type"], 0) + 1
        parts = [f"{c} {k}{'s' if c != 1 else ''}" for k, c in sorted(by_type.items(), key=lambda x: -x[1])]
        lines.append(", ".join(parts) + ".")
    else:
        lines.append("_No new transactions in the last 7 days._")
    lines.append("")

    # Risers
    if prev and risers:
        lines.append("## Top 10 dynasty risers")
        lines.append("")
        lines.append("| Player | Pos | Owner | Dyn Δ | Rank Δ |")
        lines.append("|---|---|---|---:|---:|")
        for m in risers:
            p = m["p"]
            owner = p.get("owner_name") or "FA"
            rk_d = m["rk_d"]
            rk_str = f"+{rk_d}" if rk_d > 0 else f"{rk_d}" if rk_d < 0 else "—"
            lines.append(
                f"| {p.get('full_name','?')} | {p.get('position','')} | {owner} | "
                f"{fmt_delta(m['ds_d'])} | {rk_str} |"
            )
        lines.append("")

    # Fallers
    if prev and fallers:
        lines.append("## Top 10 dynasty fallers")
        lines.append("")
        lines.append("| Player | Pos | Owner | Dyn Δ | Rank Δ |")
        lines.append("|---|---|---|---:|---:|")
        for m in fallers:
            p = m["p"]
            owner = p.get("owner_name") or "FA"
            rk_d = m["rk_d"]
            rk_str = f"+{rk_d}" if rk_d > 0 else f"{rk_d}" if rk_d < 0 else "—"
            lines.append(
                f"| {p.get('full_name','?')} | {p.get('position','')} | {owner} | "
                f"{fmt_delta(m['ds_d'])} | {rk_str} |"
            )
        lines.append("")

    # My team
    lines.append("## Your roster (mmmatlock)")
    if my_movers:
        lines.append("")
        lines.append("| Player | Pos | Dynasty Score Δ |")
        lines.append("|---|---|---:|")
        for p, d in my_movers[:15]:
            lines.append(f"| {p['full_name']} | {p['position']} | {fmt_delta(d)} |")
        lines.append("")
    else:
        lines.append("_No meaningful score changes on your roster this week._")
        lines.append("")

    # New entries (rookies, callups)
    if prev and new_players:
        lines.append("## New entries to the rankings")
        lines.append("")
        for p in new_players:
            ds = p.get("dynasty_score")
            owner = p.get("owner_name") or "FA"
            ds_str = f"{ds:.1f}" if ds is not None else "NA"
            lines.append(f"- **{p['full_name']}** ({p['position']}) — dyn {ds_str} — {owner}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"*Generated automatically by weekly_digest.py at {dt.datetime.now().isoformat(timespec='seconds')}.*")

    out.write_text("\n".join(lines))
    return out


def main() -> None:
    SNAPSHOTS.mkdir(parents=True, exist_ok=True)

    # Snapshot today's rankings_data.json (if present) before diffing
    rankings_src = PROJECT / "platform" / "rankings_data.json"
    today = dt.date.today().isoformat()
    target = SNAPSHOTS / f"rankings_{today}.json"
    if rankings_src.exists() and not target.exists():
        target.write_bytes(rankings_src.read_bytes())
        print(f"snapshotted → {target}")

    curr_path, prev_path = latest_two_snapshots()
    if curr_path is None:
        print("no snapshots available — skipping digest")
        return

    curr = load_snap(curr_path)
    prev = load_snap(prev_path) if prev_path else None
    me = curr.get("meta", {}).get("my_user_id", ME_DEFAULT)

    out_path = write_digest(prev, curr, me)
    print(out_path)


if __name__ == "__main__":
    main()
