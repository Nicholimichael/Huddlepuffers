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


def transactions_since(conn: sqlite3.Connection, since: dt.date,
                       league_id: str | None = None) -> list[dict]:
    """Transactions in the window, scoped to the CURRENT league (the table holds
    the whole dynasty chain — unscoped counts silently mix seasons)."""
    cur = conn.cursor()
    ts = int(dt.datetime.combine(since, dt.time.min).timestamp())
    try:
        cur.execute(
            """
            SELECT type, status, created FROM transactions
            WHERE created/1000 >= ? AND _league_id = ?
            ORDER BY created DESC LIMIT 200
            """, (ts, league_id or config.CURRENT_LEAGUE_ID))
    except sqlite3.OperationalError:  # old DB without _league_id
        cur.execute(
            """
            SELECT type, status, created FROM transactions
            WHERE created/1000 >= ? ORDER BY created DESC LIMIT 200
            """, (ts,))
    return [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]


def _owner_names(conn: sqlite3.Connection, league_id: str) -> dict[int, str]:
    """roster_id -> display_name for one league."""
    try:
        rows = conn.execute(
            """
            SELECT r.roster_id, u.display_name
            FROM rosters r JOIN users u
              ON u.user_id = r.owner_id AND u._league_id = r._league_id
            WHERE r._league_id = ?
            """, (league_id,)).fetchall()
        return {int(rid): name for rid, name in rows}
    except sqlite3.OperationalError:
        return {}


def _player_names(conn: sqlite3.Connection, pids: set[str]) -> dict[str, str]:
    out = {}
    for pid in pids:
        try:
            row = conn.execute(
                "SELECT full_name, position FROM players WHERE player_id = ?",
                (pid,)).fetchone()
            if row and row[0]:
                out[pid] = f"{row[0]} ({row[1] or '?'})"
        except sqlite3.OperationalError:
            break
    return out


def trade_details(conn: sqlite3.Connection, since: dt.date,
                  league_id: str) -> list[str]:
    """Human-readable one-liners for each trade in the window, with player names
    and picks. The transactions table stores adds/drops as exploded per-player
    columns (adds_<pid> = receiving roster_id), so read trade rows as full dicts."""
    ts = int(dt.datetime.combine(since, dt.time.min).timestamp())
    try:
        cur = conn.execute(
            "SELECT * FROM transactions WHERE type='trade' AND status='complete' "
            "AND created/1000 >= ? AND _league_id = ? ORDER BY created DESC",
            (ts, league_id))
    except sqlite3.OperationalError:
        return []
    cols = [d[0] for d in cur.description]
    owners = _owner_names(conn, league_id)
    lines = []
    for row in cur.fetchall():
        t = dict(zip(cols, row))
        # adds_<pid> columns: value = roster_id that RECEIVES player <pid>
        received: dict[int, list[str]] = {}
        pids = set()
        for k, v in t.items():
            if k.startswith("adds_") and v is not None and v == v:  # not None/NaN
                pid = k[5:]
                pids.add(pid)
                received.setdefault(int(v), []).append(pid)
        names = _player_names(conn, pids)
        # picks: draft_picks JSON — owner_id = receiving roster_id
        try:
            picks = json.loads(t.get("draft_picks") or "[]")
        except (TypeError, ValueError):
            picks = []
        for pk in picks:
            rid = pk.get("owner_id")
            if rid is not None:
                received.setdefault(int(rid), []).append(
                    f"{pk.get('season')} R{pk.get('round')} pick")
        if not received:
            continue
        when = dt.datetime.fromtimestamp((t.get("created") or 0) / 1000).strftime("%m/%d")
        sides = []
        for rid, assets in sorted(received.items()):
            who = owners.get(rid, f"roster {rid}")
            named = [names.get(a, a) if not a.endswith("pick") else a for a in assets]
            sides.append(f"**{who}** gets {', '.join(named)}")
        lines.append(f"- {when} trade: " + " · ".join(sides))
    return lines


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

    # Transactions — scoped to the league this snapshot was built from
    league_id = curr.get("meta", {}).get("league_id") or config.CURRENT_LEAGUE_ID
    txns, trade_lines = [], []
    if DB.exists():
        try:
            conn = sqlite3.connect(DB)
            txns = transactions_since(conn, today - dt.timedelta(days=7), league_id)
            trade_lines = trade_details(conn, today - dt.timedelta(days=7), league_id)
            conn.close()
        except Exception as e:
            print(f"warning: transaction lookup failed ({e}) — digest ships without activity")

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
        if trade_lines:
            lines.append("")
            lines.extend(trade_lines)
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
    my_name = curr.get("meta", {}).get("my_display_name") or "me"
    lines.append(f"## Your roster ({my_name})")
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

    # League-rollover guard: never diff snapshots from different leagues (a 2025
    # snapshot vs a 2026 build produces garbage movers). Walk back to the most
    # recent snapshot from the SAME league; if none, treat as a fresh baseline.
    curr_league = curr.get("meta", {}).get("league_id")
    if prev and prev.get("meta", {}).get("league_id") != curr_league:
        prev = None
        for cand in sorted(SNAPSHOTS.glob("rankings_*.json"))[-10:-1][::-1]:
            snap = load_snap(cand)
            if snap.get("meta", {}).get("league_id") == curr_league and cand != curr_path:
                prev = snap
                break
        if prev is None:
            print(f"league rolled over ({curr_league}) — no same-league prior snapshot; "
                  "baseline reset, no week-over-week compare this run")

    me = curr.get("meta", {}).get("my_user_id", ME_DEFAULT)

    out_path = write_digest(prev, curr, me)
    print(out_path)


if __name__ == "__main__":
    main()
