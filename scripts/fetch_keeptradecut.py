"""
fetch_keeptradecut.py — Pull dynasty + redraft trade values from KeepTradeCut.

KTC doesn't publish a public API, but their /dynasty-rankings and /fantasy-rankings
pages embed the full player array as a JavaScript literal:

    var playersArray = [...];

We pull the page, regex out that array, parse it as JSON, and write rows to
SQLite + CSV with the same shape as fetch_fantasycalc.py so build_rankings.py
can blend the two cleanly.

Huddlepuffers league settings (1QB, full PPR, 10-team, no TEP) drive the value
keys we pluck:
  - dynasty page → oneQBValues.value      (dynasty value)
from __future__ import annotations
  - fantasy page → oneQBValues.value      (redraft / win-now value)

KTC players don't carry Sleeper IDs in the embedded array — we crosswalk on
(normalized full_name, position) against the existing `players` table during
the blend step in build_rankings.py.

Outputs:
  - data/raw/keeptradecut_dynasty.json   : raw playersArray (dynasty)
  - data/raw/keeptradecut_redraft.json   : raw playersArray (redraft)
  - data/csv/keeptradecut_values.csv     : flattened, dynasty + redraft joined
  - db/fantasy.sqlite : ktc_values table

Usage:
    python3 fetch_keeptradecut.py
"""

import json
import re
import sqlite3
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

import pandas as pd

# ---------- CONFIG ----------
# Huddlepuffers: 1 QB, full PPR, 10-team, no TEP.
# KTC's embedded array carries values for every format; we pluck the right keys.
SUPERFLEX = False              # False = 1QB. KTC default landing page is Superflex.
TE_PREMIUM = "OFF"             # OFF | TE+ | TE++ | TE+++
# ----------------------------

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
CSV = ROOT / "data" / "csv"
DB_PATH = ROOT / "db" / "fantasy.sqlite"
for d in (RAW, CSV, DB_PATH.parent):
    d.mkdir(parents=True, exist_ok=True)

DYNASTY_URL = "https://keeptradecut.com/dynasty-rankings"
REDRAFT_URL = "https://keeptradecut.com/fantasy-rankings"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

PLAYERS_ARRAY_RE = re.compile(r"var\s+playersArray\s*=\s*(\[.+?\]);", re.DOTALL)


def fetch(url, retries=3):
    """Fetch via curl — macOS curl handles modern TLS; system Python 3.9 OpenSSL is too old for KTC."""
    import subprocess
    for i in range(retries):
        try:
            result = subprocess.run(
                ["curl", "-sL", "--fail", "--max-time", "30",
                 "-A", HEADERS["User-Agent"],
                 "-H", "Accept: " + HEADERS["Accept"],
                 "-H", "Accept-Language: " + HEADERS["Accept-Language"],
                 url],
                capture_output=True, text=True, check=True,
            )
            return result.stdout
        except subprocess.CalledProcessError:
            if i == retries - 1:
                raise
            time.sleep(1.5 ** i)
    raise RuntimeError("Exhausted retries for " + url)


def extract_players_array(html: str) -> list:
    """Pull the playersArray JS literal out of a KTC page."""
    m = PLAYERS_ARRAY_RE.search(html)
    if not m:
        raise ValueError(
            "playersArray not found in page source — KTC may have changed their "
            "DOM. Inspect the raw HTML and update PLAYERS_ARRAY_RE."
        )
    return json.loads(m.group(1))


def value_for_format(player: dict, superflex: bool, te_premium: str):
    """
    Walk KTC's nested value object for the format we care about.

    KTC embeds values like:
      player["superflexValues"][tePremiumKey] = { "value": ..., "rank": ..., ... }
      player["oneQBValues"][tePremiumKey]     = { "value": ..., "rank": ..., ... }

    tePremiumKey is one of: "value" (OFF), "tePremium" (TE+), "tePremiumPlus" (TE++).

    Returns the leaf dict or None if the shape doesn't match (some entries — e.g.
    rookies before their first KTC vote — won't have a value).
    """
    bucket = "superflexValues" if superflex else "oneQBValues"
    if bucket not in player or not isinstance(player[bucket], dict):
        return None

    tep_key = {
        "OFF": "value",
        "TE+": "tePremium",
        "TE++": "tePremiumPlus",
        "TE+++": "tePremiumPlusPlus",
    }.get(te_premium, "value")

    leaf = player[bucket]
    # Some KTC schemas put scalars directly under the bucket, others nest one more
    # level under tep_key. Handle both.
    if isinstance(leaf.get(tep_key), dict):
        return leaf[tep_key]
    return leaf


def parse_rows(players: list, kind: str):
    """Flatten KTC's nested array into one row per (player, kind) pair."""
    rows = []
    for p in players:
        v = value_for_format(p, SUPERFLEX, TE_PREMIUM)
        if not v:
            continue
        rows.append({
            "ktc_id": p.get("playerID") or p.get("id"),
            "full_name": p.get("playerName") or p.get("name"),
            "position": p.get("position"),
            "team": p.get("team"),
            "age": p.get("age"),
            "kind": kind,                                     # "dynasty" | "redraft"
            "value": v.get("value"),
            "overall_rank": v.get("overallRank") or v.get("rank"),
            "position_rank": v.get("positionalRank") or v.get("positionRank"),
            "tier": v.get("tier"),
            "trend_30day": v.get("overallTrend") or v.get("trend30Day"),
        })
    return rows


def main() -> None:
    fmt = "Superflex" if SUPERFLEX else "1QB"
    print(f"Pulling KeepTradeCut: format={fmt} tep={TE_PREMIUM}")

    # --- Dynasty values ---
    print(f"  fetching {DYNASTY_URL}")
    dyn_html = fetch(DYNASTY_URL)
    dyn_players = extract_players_array(dyn_html)
    (RAW / "keeptradecut_dynasty.json").write_text(json.dumps(dyn_players, indent=2, default=str))
    dyn_rows = parse_rows(dyn_players, "dynasty")
    print(f"    {len(dyn_players)} entries in array, {len(dyn_rows)} with values")

    # --- Redraft values ---
    print(f"  fetching {REDRAFT_URL}")
    red_html = fetch(REDRAFT_URL)
    red_players = extract_players_array(red_html)
    (RAW / "keeptradecut_redraft.json").write_text(json.dumps(red_players, indent=2, default=str))
    red_rows = parse_rows(red_players, "redraft")
    print(f"    {len(red_players)} entries in array, {len(red_rows)} with values")

    # Fail loud if either side comes back empty — that means KTC's DOM shifted.
    if not dyn_rows or not red_rows:
        print("ERROR: empty rows from KTC — bailing without writing DB", file=sys.stderr)
        sys.exit(1)

    # --- Combine & pivot to one row per player ---
    df = pd.DataFrame(dyn_rows + red_rows)
    pivot = df.pivot_table(
        index=["ktc_id", "full_name", "position", "team", "age"],
        columns="kind",
        values=["value", "overall_rank", "position_rank", "tier", "trend_30day"],
        aggfunc="first",
    )
    pivot.columns = [f"{kind}_{metric}" for metric, kind in pivot.columns]
    pivot = pivot.reset_index()

    # Standardize column names to match fantasycalc_values conventions.
    pivot = pivot.rename(columns={
        "dynasty_value":         "ktc_dyn",
        "redraft_value":         "ktc_red",
        "dynasty_overall_rank":  "ktc_dyn_rank",
        "redraft_overall_rank":  "ktc_red_rank",
        "dynasty_position_rank": "ktc_dyn_pos_rank",
        "redraft_position_rank": "ktc_red_pos_rank",
        "dynasty_trend_30day":   "ktc_dyn_trend_30day",
        "redraft_trend_30day":   "ktc_red_trend_30day",
        "dynasty_tier":          "ktc_dyn_tier",
        "redraft_tier":          "ktc_red_tier",
    })

    pivot.to_csv(CSV / "keeptradecut_values.csv", index=False)

    conn = sqlite3.connect(DB_PATH)
    pivot.to_sql("ktc_values", conn, if_exists="replace", index=False)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ktc_name ON ktc_values(full_name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ktc_pos  ON ktc_values(position)")
    conn.commit()
    conn.close()
    print(f"  wrote {len(pivot):,} rows -> csv + db (ktc_values)")


if __name__ == "__main__":
    main()
