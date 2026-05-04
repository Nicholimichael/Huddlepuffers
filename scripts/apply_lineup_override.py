"""Apply manual_lineup_override.json onto rankings_data.json.

Why this exists:
  Sleeper's /league/{id}/rosters endpoint returns the lineup from the most recent
  scored matchup — which during the NFL offseason is the last regular-season week.
  The user's current "set for next season" lineup (visible in the Sleeper app) is
  stored in a different place that isn't exposed via the public rosters API.

  This script lets us override the dashboard's starter / taxi / reserve flags for
  the user's roster using a hand-edited JSON file. Run this AFTER build_platform_v2.py
  (which produces rankings_data.json) and BEFORE build_artifact_v2.py.

  IMPORTANT: this file lives in scripts/ — NOT platform/ — because platform/ is
  the directory Netlify deploys to the CDN. Putting a .py file there causes
  Netlify to try to publish it and the deploy fails with a 422.

Usage:
  python3 scripts/apply_lineup_override.py
"""
from __future__ import annotations
import json
import os
import sys
from datetime import datetime, timezone

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPTS_DIR)
PLATFORM_DIR = os.path.join(PROJECT_ROOT, "platform")
RANKINGS_PATH = os.path.join(PLATFORM_DIR, "rankings_data.json")
OVERRIDE_PATH = os.path.join(SCRIPTS_DIR, "manual_lineup_override.json")


def main() -> int:
    if not os.path.exists(OVERRIDE_PATH):
        print("No manual_lineup_override.json found — skipping override.")
        return 0

    with open(RANKINGS_PATH) as f:
        rankings = json.load(f)
    with open(OVERRIDE_PATH) as f:
        override = json.load(f)

    owner_id = override["owner_id"]
    owner_name = override["owner_name"]
    starter_ids = {p["player_id"] for p in override["starters"]}
    taxi_ids = {p["player_id"] for p in override["taxi"]}
    reserve_ids = {p["player_id"] for p in override["reserve"]}
    extra_ids = {p["player_id"] for p in override.get("extra_roster_players", [])}

    full_roster = starter_ids | taxi_ids | reserve_ids | extra_ids
    # Also include current rankings_data players already owned by this user so we
    # don't accidentally drop anyone the user still rosters.
    existing_owned = {p["player_id"] for p in rankings["players"] if p.get("owner_id") == owner_id}
    full_roster |= existing_owned

    starters_set, taxi_set, reserve_set = 0, 0, 0
    extras_added = 0

    for p in rankings["players"]:
        pid = p["player_id"]
        if pid in full_roster:
            # Force ownership in case it shifted
            p["owner_id"] = owner_id
            p["owner_name"] = owner_name
            p["rostered"] = True
            p["is_starter"] = pid in starter_ids
            p["is_taxi"] = pid in taxi_ids
            p["is_reserve"] = pid in reserve_ids
            if p["is_starter"]:
                starters_set += 1
            if p["is_taxi"]:
                taxi_set += 1
            if p["is_reserve"]:
                reserve_set += 1
            if pid in extra_ids and pid not in existing_owned:
                extras_added += 1
        elif p.get("owner_id") == owner_id:
            # Player was on user's roster in the API but isn't in the override —
            # leave the owner_id alone (they may still be on the roster) but
            # clear starter/taxi/reserve flags since they're not in the new lineup.
            p["is_starter"] = False

    # Recompute team-level aggregates for the user's team
    nick_players = [p for p in rankings["players"] if p.get("owner_id") == owner_id]
    nick_starters = [p for p in nick_players if p.get("is_starter")]
    s_dyn = sum((p.get("dynasty_score") or 0) for p in nick_starters)
    s_win = sum((p.get("winnow_score") or 0) for p in nick_starters)

    for t in rankings["teams"]:
        if t.get("owner_id") == owner_id:
            t["starters_dynasty"] = round(s_dyn, 1)
            t["starters_winnow"] = round(s_win, 1)
            t["roster_size"] = len(nick_players)

    # Stamp meta so we know the override ran
    rankings["meta"]["lineup_override_applied_at"] = datetime.now(timezone.utc).isoformat()
    rankings["meta"]["lineup_override_source"] = "scripts/manual_lineup_override.json"
    rankings["meta"]["lineup_override_as_of"] = override.get("as_of")

    with open(RANKINGS_PATH, "w") as f:
        json.dump(rankings, f, indent=2)

    print(
        f"✓ Lineup override applied — starters={starters_set} taxi={taxi_set} "
        f"reserve={reserve_set} extras_added={extras_added}"
    )
    print(f"  Owner: {owner_name} ({owner_id})")
    print(f"  starters_dynasty: {round(s_dyn,1)}, starters_winnow: {round(s_win,1)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
