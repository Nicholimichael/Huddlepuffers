#!/usr/bin/env python3
"""
verify_rosters.py — Ground-truth check of the built data against live Sleeper (v3/B1).

This is the check that would have caught the 2026 season freeze months earlier:
after the build (and before deploy), pull the CURRENT league's rosters straight
from the Sleeper API and assert that every rostered player in rankings_data.json
is on the roster Sleeper says they're on. Any drift — wrong league, missed trade,
stale rosters — fails the workflow BEFORE the deploy step.

Network failure is a warn-and-pass (a flaky API must not block a good deploy);
a successful API response with mismatched data is a hard fail.

Exit 0 = verified (or skipped on network error). Exit 1 = data does not match Sleeper.
"""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import config  # noqa: E402

RANKINGS = ROOT / "platform" / "rankings_data.json"
API = "https://api.sleeper.app/v1"


def get_json(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "huddlepuffers-refresh"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def main():
    data = json.load(open(RANKINGS))
    meta = data["meta"]
    league_id = str(meta.get("league_id"))

    if league_id != str(config.CURRENT_LEAGUE_ID):
        print(f"::error::[verify_rosters] built data is for league {league_id}, "
              f"config says {config.CURRENT_LEAGUE_ID}")
        return 1

    try:
        rosters = get_json(f"{API}/league/{league_id}/rosters")
        users = get_json(f"{API}/league/{league_id}/users")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as e:
        print(f"::warning::[verify_rosters] Sleeper unreachable ({type(e).__name__}: {e}) "
              "— skipping ground-truth check this run.")
        return 0

    if len(rosters) != len(data["teams"]):
        print(f"::error::[verify_rosters] Sleeper has {len(rosters)} rosters, "
              f"built data has {len(data['teams'])} teams")
        return 1

    # Ground truth: player_id -> owner_id straight from Sleeper.
    truth = {}
    for r in rosters:
        for pid in (r.get("players") or []):
            truth[str(pid)] = r.get("owner_id")

    display = {u["user_id"]: u.get("display_name") for u in users}
    mismatches = []
    checked = 0
    for p in data["players"]:
        if not p.get("owner_id"):
            continue  # free agent in our data — nothing to verify
        checked += 1
        actual = truth.get(str(p["player_id"]))
        if actual != p["owner_id"]:
            mismatches.append(
                f"{p.get('full_name')} ({p.get('player_id')}): data says "
                f"{p.get('owner_name')}, Sleeper says "
                f"{display.get(actual, actual or 'FA/not rostered')}")

    if mismatches:
        print(f"::error::[verify_rosters] {len(mismatches)}/{checked} rostered players "
              "do not match live Sleeper — refusing to deploy stale rosters:")
        for m in mismatches[:15]:
            print(f"::error::  {m}")
        return 1

    print(f"[verify_rosters] OK — {checked} rostered players match live Sleeper "
          f"rosters for league {league_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
