#!/usr/bin/env python3
"""
validate_data.py — Schema gate for the built league data (v3/B3).

Runs after the build steps and BEFORE build_redesign.py in the weekly workflow.
Validates platform/rankings_data.json and platform/ai_labels.json against the
shapes the dashboard actually depends on, so a malformed build fails loudly
instead of deploying a broken page. Stdlib only — no jsonschema dependency.

Exit 0 = valid. Exit 1 = validation failure (fails the workflow pre-deploy).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import config  # noqa: E402

RANKINGS = ROOT / "platform" / "rankings_data.json"
LABELS = ROOT / "platform" / "ai_labels.json"

TEAM_REQUIRED = ["roster_id", "owner_id", "owner_name", "wins", "losses",
                 "dynasty_total", "winnow_total", "roster_size"]
PLAYER_REQUIRED = ["player_id", "full_name", "position", "owner_id",
                   "dynasty_score", "winnow_score"]
TONE_FIELDS = ["nickname_friendly", "blurb_friendly", "nickname_spicy", "blurb_spicy"]

errors: list[str] = []
warnings: list[str] = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def check_rankings():
    if not RANKINGS.exists():
        err(f"{RANKINGS} does not exist")
        return
    try:
        data = json.load(open(RANKINGS))
    except Exception as e:
        err(f"rankings_data.json is not valid JSON: {e}")
        return

    for k in ("meta", "teams", "players", "picks"):
        if k not in data:
            err(f"rankings_data.json missing top-level key: {k}")
    if errors:
        return

    meta = data["meta"]
    if str(meta.get("league_id")) != str(config.CURRENT_LEAGUE_ID):
        err(f"meta.league_id = {meta.get('league_id')} but config says "
            f"{config.CURRENT_LEAGUE_ID} — build is anchored to the wrong league")
    if str(meta.get("season")) != config.CURRENT_SEASON_STR:
        err(f"meta.season = {meta.get('season')}, config says {config.CURRENT_SEASON}")
    if not meta.get("generated_at"):
        err("meta.generated_at missing")

    teams = data["teams"]
    if len(teams) != 10:
        err(f"expected 10 teams, got {len(teams)}")
    for t in teams:
        missing = [k for k in TEAM_REQUIRED if k not in t]
        if missing:
            err(f"team {t.get('owner_name', '?')} missing fields: {missing}")
    if not any(t.get("is_me") for t in teams):
        err("no team flagged is_me — my-team views will be empty")

    players = data["players"]
    if len(players) < 300:
        err(f"only {len(players)} players — pipeline likely lost a source")
    bad = [p.get("full_name") for p in players[:50]
           if any(k not in p for k in PLAYER_REQUIRED)]
    if bad:
        err(f"players missing required fields (sample): {bad[:5]}")

    rostered = sum(1 for p in players if p.get("owner_id"))
    if rostered < 250:
        err(f"only {rostered} rostered players — rosters look truncated "
            f"(10 teams x ~30 should be ~300)")

    if not data["picks"]:
        warn("picks list is empty — Picks view will be blank")

    hof = (data.get("extras") or {}).get("hall_of_fame") or {}
    if not hof.get("available") or not hof.get("seasons"):
        warn("extras.hall_of_fame missing/empty — Hall of Fame tab will show a placeholder")
    elif len(hof.get("franchises", [])) != 10:
        warn(f"hall_of_fame has {len(hof.get('franchises', []))} franchises (expected 10)")


def check_labels():
    if not LABELS.exists():
        warn(f"{LABELS} missing — dashboard falls back to stat-template copy")
        return
    try:
        labels = json.load(open(LABELS))
    except Exception as e:
        err(f"ai_labels.json is not valid JSON: {e}")
        return
    team_labels = labels.get("teams", {})
    if len(team_labels) < 10:
        warn(f"ai_labels has {len(team_labels)} teams (expected 10)")
    missing_tones = {o: [f for f in TONE_FIELDS if not L.get(f)]
                     for o, L in team_labels.items()}
    missing_tones = {o: m for o, m in missing_tones.items() if m}
    if missing_tones:
        # Tone fields are what keep the Friendly/Spicy toggle alive — regressing
        # them is exactly the failure v3 was built to prevent, so this is FATAL.
        err(f"ai_labels teams missing tone fields (toggle would silently break): "
            f"{missing_tones}")
    if not labels.get("state_of_league"):
        warn("ai_labels.state_of_league missing")


def main():
    check_rankings()
    check_labels()
    for w in warnings:
        print(f"::warning::[validate_data] {w}")
    if errors:
        for e in errors:
            print(f"::error::[validate_data] {e}")
        return 1
    print(f"[validate_data] OK — rankings_data.json and ai_labels.json pass "
          f"({len(warnings)} warnings)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
