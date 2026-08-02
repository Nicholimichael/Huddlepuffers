"""
fetch_fantasycalc.py — Pull dynasty trade values from the FantasyCalc public API.

FantasyCalc exposes a free public endpoint that returns community-sourced
dynasty/redraft trade values. Results include Sleeper IDs so they join
cleanly to our existing Sleeper data.

Outputs:
  - data/csv/fantasycalc_values.csv    : current trade values
  - db/fantasy.sqlite : fantasycalc_values table

Usage:
    python3 fetch_fantasycalc.py
"""

import json
import sqlite3
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

import pandas as pd

# ---------- CONFIG ----------
# Huddlepuffers settings: 10-team, 1 QB, IDP — closest FantasyCalc preset is standard dynasty
IS_DYNASTY = "true"
NUM_QBS = 1               # 1 = single QB leagues; use 2 for superflex
NUM_TEAMS = 10
PPR = 1                    # 1 = full PPR; 0.5 for half; 0 for standard
# ----------------------------

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
CSV = ROOT / "data" / "csv"
DB_PATH = ROOT / "db" / "fantasy.sqlite"
for d in (RAW, CSV, DB_PATH.parent):
    d.mkdir(parents=True, exist_ok=True)

URL = (
    f"https://api.fantasycalc.com/values/current"
    f"?isDynasty={IS_DYNASTY}&numQbs={NUM_QBS}&numTeams={NUM_TEAMS}&ppr={PPR}"
)


def get(url, retries=3):
    for i in range(retries):
        try:
            req = Request(url, headers={"User-Agent": "HossAutomation-FantasyFootball/1.0"})
            with urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except (HTTPError, URLError) as e:
            if i == retries - 1:
                raise
            time.sleep(1.5 ** i)


def main():
    print(f"Pulling FantasyCalc: dynasty={IS_DYNASTY} qbs={NUM_QBS} teams={NUM_TEAMS} ppr={PPR}")
    data = get(URL)
    print(f"  {len(data)} entries returned")

    (RAW / "fantasycalc_values.json").write_text(json.dumps(data, indent=2, default=str))

    rows = []
    for item in data:
        player = item.get("player") or {}
        rows.append({
            "fantasycalc_id": player.get("id"),
            "sleeper_id": player.get("sleeperId"),
            "mfl_id": player.get("mflId"),
            "espn_id": player.get("espnId"),
            "fleaflicker_id": player.get("fleaflickerId"),
            "full_name": player.get("name"),
            "position": player.get("position"),
            "team": player.get("maybeTeam"),
            "age": player.get("maybeAge"),
            "birthday": player.get("maybeBirthday"),
            "draft_year": player.get("maybeYearsExperience"),
            "value": item.get("value"),
            "overall_rank": item.get("overallRank"),
            "position_rank": item.get("positionRank"),
            "trend_30day": item.get("trend30Day"),
            "redraft_value": item.get("redraftValue"),
            "combined_value": item.get("combinedValue"),
            "redraft_rank": item.get("redraftRank"),
            "redraft_position_rank": item.get("redraftPositionRank"),
            "starter_value": item.get("starterValue"),
            "playoff_value": item.get("playoffValue"),
        })

    df = pd.DataFrame(rows)

    # v3/B6 guard: a suspiciously small pull means FantasyCalc changed their API
    # or returned junk — refuse to overwrite a good table with a bad one.
    MIN_ROWS = 350
    if len(df) < MIN_ROWS:
        print(f"::warning::[fetch_fantasycalc] only {len(df)} rows (expected ~450+, "
              f"floor {MIN_ROWS}) — keeping the previous fantasycalc_values table")
        raise SystemExit(1)

    df.to_csv(CSV / "fantasycalc_values.csv", index=False)

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("fantasycalc_values", conn, if_exists="replace", index=False)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fc_sleeper ON fantasycalc_values(sleeper_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fc_pos ON fantasycalc_values(position)")
    conn.commit()
    conn.close()
    print(f"  wrote {len(df):,} rows -> csv + db")


if __name__ == "__main__":
    main()
