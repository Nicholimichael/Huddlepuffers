#!/usr/bin/env python3
"""
check_season.py — Guard against a silent dynasty-season rollover.

fetch_sleeper.py walks the whole dynasty chain and stores EVERY season's league in
the `leagues` table — including a newly-created next-season league. But the build
pins everything to config.CURRENT_SEASON. So when the dynasty rolls to a new season
and config.py is NOT updated, the pipeline keeps deploying last year's standings
forever: green runs, stale site, no error.

This guard fails the run LOUDLY (which trips the failure-alert SMS) the moment the
DB contains a season newer than CURRENT_SEASON — turning a silent freeze into a
visible, actionable failure. When it fires: bump CURRENT_SEASON / CURRENT_LEAGUE_ID
in config.py (the next league_id is noted there), then re-run.

Exit 0 = current. Exit 1 = rollover detected, config is behind.
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root → import config
import config  # noqa: E402


def main():
    try:
        con = sqlite3.connect(config.DB_PATH)
        rows = con.execute("SELECT season FROM leagues").fetchall()
    except Exception as e:  # DB missing/locked — don't false-alarm, just skip
        print(f"::warning::check_season could not read leagues ({e}); skipping guard.")
        return 0

    seasons = []
    for (s,) in rows:
        try:
            seasons.append(int(s))
        except (TypeError, ValueError):
            pass
    if not seasons:
        print("::warning::no seasons in leagues table; skipping season guard.")
        return 0

    latest = max(seasons)
    if latest > config.CURRENT_SEASON:
        print(
            f"::error::Dynasty has rolled to season {latest}, but config.CURRENT_SEASON "
            f"is still {config.CURRENT_SEASON}. The dashboard would freeze on "
            f"{config.CURRENT_SEASON}. Update CURRENT_SEASON + CURRENT_LEAGUE_ID in "
            f"config.py (the {latest} league_id is noted there), then re-run."
        )
        return 1

    print(f"[check_season] OK — config season {config.CURRENT_SEASON} is current "
          f"(latest league in DB: {latest}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
