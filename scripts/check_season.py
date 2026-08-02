#!/usr/bin/env python3
"""
check_season.py — Guard against a silent dynasty-season rollover.

The build pins everything to config.CURRENT_SEASON / CURRENT_LEAGUE_ID. When the
dynasty rolls to a new Sleeper season and config.py is NOT updated, the pipeline
keeps deploying last year's rosters forever: green runs, stale site, no error.
That exact failure happened over summer 2026 — the previous version of this guard
compared config against the local DB, but fetch_sleeper.py walks the dynasty
chain BACKWARDS from CURRENT_LEAGUE_ID (via previous_league_id), so the DB could
never contain a season newer than config and the guard could never fire.

This version looks FORWARD at the Sleeper API instead:

  1. GET /v1/user/<MY_USER_ID>/leagues/nfl/<CURRENT_SEASON + 1>
     → if any league's previous_league_id == CURRENT_LEAGUE_ID, the dynasty has
       rolled over. Fail LOUDLY and print the exact config.py values to paste in.
  2. Belt-and-suspenders: GET /v1/league/<CURRENT_LEAGUE_ID> — warn if Sleeper
     reports the configured league's season differs from config, or its status is
     "complete" (season over; successor league may simply not exist yet).

Network problems must not false-alarm a refresh: any API error → warn + exit 0.

Exit 0 = current (or guard skipped on network error).
Exit 1 = rollover detected, config.py is behind.
"""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root → import config
import config  # noqa: E402

API = "https://api.sleeper.app/v1"


def get_json(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "huddlepuffers-refresh"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def main():
    next_season = config.CURRENT_SEASON + 1

    # --- 1. Forward look: does a next-season league chained to ours exist? ---
    try:
        leagues = get_json(f"{API}/user/{config.MY_USER_ID}/leagues/nfl/{next_season}") or []
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as e:
        print(f"::warning::[check_season] could not query Sleeper for {next_season} "
              f"leagues ({type(e).__name__}: {e}); skipping rollover guard this run.")
        return 0

    for lg in leagues:
        if lg.get("previous_league_id") == config.CURRENT_LEAGUE_ID:
            print(
                f"::error::Dynasty has rolled to season {next_season} "
                f"(league \"{lg.get('name')}\", league_id {lg.get('league_id')}), but "
                f"config.py still pins CURRENT_SEASON = {config.CURRENT_SEASON}. "
                f"The dashboard would freeze on {config.CURRENT_SEASON}. Update config.py:\n"
                f"    CURRENT_SEASON      = {next_season}\n"
                f"    CURRENT_LEAGUE_ID   = \"{lg.get('league_id')}\"\n"
                f"then re-run the workflow."
            )
            return 1

    # --- 2. Sanity: is the configured league itself still what Sleeper thinks? ---
    try:
        cur = get_json(f"{API}/league/{config.CURRENT_LEAGUE_ID}")
        status = (cur or {}).get("status")
        season = (cur or {}).get("season")
        if str(season) != config.CURRENT_SEASON_STR:
            print(f"::warning::[check_season] league {config.CURRENT_LEAGUE_ID} reports "
                  f"season {season}, config says {config.CURRENT_SEASON} — check config.py.")
        if status == "complete":
            print(f"::warning::[check_season] configured league status is 'complete' — the "
                  f"{config.CURRENT_SEASON} season is over. The {next_season} league may not "
                  f"be created yet; this guard will fail the run once it exists.")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as e:
        print(f"::warning::[check_season] could not verify configured league "
              f"({type(e).__name__}: {e}).")

    print(f"[check_season] OK — config season {config.CURRENT_SEASON} "
          f"(league {config.CURRENT_LEAGUE_ID}) is current; no {next_season} "
          f"successor league found on Sleeper.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
