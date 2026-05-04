"""
Build the v2 Huddlepuffers platform data JSON with the three new features:
  1. Dynasty trade value trend history (aggregated from data/snapshots/)
  2. Per-team roster construction scores (win-now/rebuild/posture)
  3. Future draft pick ownership (resolves traded_picks chain)

Input:
  - platform/rankings_data.json         (produced by build_rankings.py)
  - data/snapshots/rankings_*.json      (daily snapshots)
  - data/csv/traded_picks.csv           (pick trade history)
  - data/csv/rosters.csv                (for roster_id -> owner mapping)

Output:
  - platform/rankings_data.json         (rewritten, now includes extras)

Idempotent — safe to re-run any time after build_rankings.py.
"""
import json
import csv
import glob
import os
import sys
from collections import defaultdict
from datetime import datetime
import math
from pathlib import Path

# Make project-root config importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

PROJECT_ROOT = str(config.PROJECT_ROOT)

RANKINGS_JSON = str(config.PLATFORM_DIR / "rankings_data.json")
SNAPSHOT_GLOB = str(config.SNAPSHOTS_DIR / "rankings_*.json")
TRADED_PICKS_CSV = str(config.DATA_DIR / "csv" / "traded_picks.csv")
ROSTERS_CSV = str(config.DATA_DIR / "csv" / "rosters.csv")
USERS_CSV = str(config.DATA_DIR / "csv" / "users.csv")
OUTPUT_JSON = RANKINGS_JSON  # rewrite in place

# League constants — sourced from config.py (single source of truth)
CURRENT_LEAGUE_ID = config.CURRENT_LEAGUE_ID
MY_USER_ID = config.MY_USER_ID
ROOKIE_DRAFT_ROUNDS = 5
FUTURE_SEASONS = [config.NEXT_DRAFT_SEASON, config.NEXT_DRAFT_SEASON + 1, config.NEXT_DRAFT_SEASON + 2]

# ────────────────────────────────────────────────────────────────────────────
# Load base data
# ────────────────────────────────────────────────────────────────────────────
print(f"[1/5] Loading rankings from {RANKINGS_JSON}")
with open(RANKINGS_JSON) as f:
    data = json.load(f)

players = data["players"]
teams = data["teams"]
picks = data["picks"]

# roster_id -> owner_id / owner_name lookup (from teams)
roster_lookup = {t["roster_id"]: t for t in teams}
owner_lookup = {t["owner_id"]: t for t in teams}


from lib.utils import clean_num


# ────────────────────────────────────────────────────────────────────────────
# Feature 1: Trade value trend history
# ────────────────────────────────────────────────────────────────────────────
print(f"[2/5] Building value history from snapshots")
snapshot_files = sorted(glob.glob(SNAPSHOT_GLOB))
print(f"      Found {len(snapshot_files)} snapshot files")

history = defaultdict(list)
snapshot_dates = []
for sf in snapshot_files:
    date_str = os.path.basename(sf).replace("rankings_", "").replace(".json", "")
    try:
        with open(sf) as f:
            snap = json.load(f)
    except Exception as e:
        print(f"      skipped {sf}: {e}")
        continue
    snap_generated = snap.get("meta", {}).get("generated_at", date_str)
    snapshot_dates.append(date_str)
    for p in snap.get("players", []):
        pid = p.get("player_id")
        if not pid:
            continue
        history[pid].append({
            "date": date_str,
            "dyn": clean_num(p.get("trade_dyn_value")),
            "red": clean_num(p.get("trade_red_value")),
            "dyn_score": clean_num(p.get("dynasty_score")),
            "win_score": clean_num(p.get("winnow_score")),
            "dyn_rank": clean_num(p.get("dynasty_overall_rank")),
        })
    # also picks
    for p in snap.get("picks", []):
        pid = p.get("player_id")
        if not pid:
            continue
        history[pid].append({
            "date": date_str,
            "dyn": clean_num(p.get("trade_dyn_value")),
            "red": clean_num(p.get("trade_red_value")),
            "dyn_rank": clean_num(p.get("overall_rank")),
        })

# dedupe history by date (keep first)
for pid, rows in list(history.items()):
    seen = set()
    dedup = []
    for r in rows:
        if r["date"] in seen:
            continue
        seen.add(r["date"])
        dedup.append(r)
    history[pid] = sorted(dedup, key=lambda x: x["date"])

# Compute derived trend fields per player (FantasyCalc trend_30day is already there)
# Clean up NaN trend values
for p in players:
    p["trend_30day"] = clean_num(p.get("trend_30day"))

# Risers / fallers from trend_30day (real-time FantasyCalc signal)
risers_fallers = {"risers": [], "fallers": []}
scored = [p for p in players if p.get("trend_30day") is not None and (p.get("trade_dyn_value") or 0) >= 500]
top_risers = sorted(scored, key=lambda p: p["trend_30day"], reverse=True)[:20]
top_fallers = sorted(scored, key=lambda p: p["trend_30day"])[:20]

def slim_player_ref(p):
    return {
        "player_id": p["player_id"],
        "full_name": p["full_name"],
        "position": p["position"],
        "team": p.get("team"),
        "age": p.get("age"),
        "owner_name": p.get("owner_name"),
        "owner_id": p.get("owner_id"),
        "trade_dyn_value": clean_num(p.get("trade_dyn_value")),
        "trend_30day": clean_num(p.get("trend_30day")),
        "dynasty_score": clean_num(p.get("dynasty_score")),
        "winnow_score": clean_num(p.get("winnow_score")),
    }

risers_fallers["risers"] = [slim_player_ref(p) for p in top_risers]
risers_fallers["fallers"] = [slim_player_ref(p) for p in top_fallers]

print(f"      history tracked for {len(history)} assets across {len(snapshot_dates)} snapshots")

# ────────────────────────────────────────────────────────────────────────────
# Feature 2: Roster construction per team
# ────────────────────────────────────────────────────────────────────────────
print(f"[3/5] Computing roster construction scores")

# Group players by owner
by_owner = defaultdict(list)
for p in players:
    if p.get("owner_id"):
        by_owner[p["owner_id"]].append(p)

# Compute metrics per team
construction = []
for t in teams:
    oid = t["owner_id"]
    roster = by_owner.get(oid, [])
    starters = [p for p in roster if p.get("is_starter")]
    bench = [p for p in roster if not p.get("is_starter") and not p.get("is_taxi") and not p.get("is_reserve")]
    taxi_ir = [p for p in roster if p.get("is_taxi") or p.get("is_reserve")]

    # Age profile (weighted by dynasty_score on starters)
    start_ages = [(p.get("age") or 0, p.get("dynasty_score") or 0) for p in starters if p.get("age")]
    if start_ages:
        w = sum(s for _, s in start_ages) or 1
        avg_starter_age = sum(a * s for a, s in start_ages) / w
    else:
        avg_starter_age = None

    # Young vs aged asset buckets — offensive skill only (QB/RB/WR/TE)
    off_pos = {"QB", "RB", "WR", "TE"}
    off_roster = [p for p in roster if p.get("position") in off_pos]
    young = [p for p in off_roster if (p.get("age") or 99) <= 24]
    aged = [p for p in off_roster if (p.get("age") or 0) >= 29]
    young_dyn_sum = sum(p.get("dynasty_score") or 0 for p in young)
    aged_dyn_sum = sum(p.get("dynasty_score") or 0 for p in aged)

    # Position totals + ranks (computed later across league)
    pos_totals = {}
    for pos in ["QB", "RB", "WR", "TE", "K", "DEF", "DL", "LB", "DB"]:
        pos_players = [p for p in roster if p.get("position") == pos]
        pos_starters = [p for p in pos_players if p.get("is_starter")]
        pos_totals[pos] = {
            "dynasty_sum": sum(p.get("dynasty_score") or 0 for p in pos_players),
            "winnow_sum": sum(p.get("winnow_score") or 0 for p in pos_players),
            "starter_winnow": sum(p.get("winnow_score") or 0 for p in pos_starters),
            "starter_dynasty": sum(p.get("dynasty_score") or 0 for p in pos_starters),
            "depth": len(pos_players),
            "starters": len(pos_starters),
        }

    construction.append({
        "roster_id": t["roster_id"],
        "owner_id": oid,
        "owner_name": t.get("owner_name"),
        "wins": t.get("wins"),
        "losses": t.get("losses"),
        "is_me": oid == MY_USER_ID,
        "starters_winnow": t.get("starters_winnow"),
        "starters_dynasty": t.get("starters_dynasty"),
        "winnow_total": t.get("winnow_total"),
        "dynasty_total": t.get("dynasty_total"),
        "avg_starter_age": round(avg_starter_age, 1) if avg_starter_age else None,
        "young_dyn_sum": round(young_dyn_sum, 1),
        "aged_dyn_sum": round(aged_dyn_sum, 1),
        "young_count": len(young),
        "aged_count": len(aged),
        "roster_size": len(roster),
        "starters_count": len(starters),
        "pos_totals": pos_totals,
    })

# League-wide normalization
def pct_rank(values, v):
    """Return 0-100 percentile rank of v among values (higher = better)."""
    if v is None:
        return 50.0
    ranked = sorted(values)
    n = len(ranked)
    if n == 0:
        return 50.0
    # percentile = proportion of values <= v
    below = sum(1 for x in ranked if x < v)
    eq = sum(1 for x in ranked if x == v)
    return round((below + eq * 0.5) / n * 100, 1)

all_starters_winnow = [c["starters_winnow"] or 0 for c in construction]
all_young_dyn = [c["young_dyn_sum"] for c in construction]
all_dyn_total = [c["dynasty_total"] or 0 for c in construction]

# Position ranks — for each pos, who has the most dynasty_sum / starter_winnow
pos_ranks = defaultdict(dict)  # pos_ranks[pos][owner_id] = {dyn_rank, win_rank}
for pos in ["QB", "RB", "WR", "TE", "K", "DEF", "DL", "LB", "DB"]:
    dyn_sorted = sorted(construction, key=lambda c: c["pos_totals"][pos]["dynasty_sum"], reverse=True)
    win_sorted = sorted(construction, key=lambda c: c["pos_totals"][pos]["starter_winnow"], reverse=True)
    for i, c in enumerate(dyn_sorted):
        pos_ranks[pos][c["owner_id"]] = {"dyn_rank": i + 1, "dyn_sum": c["pos_totals"][pos]["dynasty_sum"]}
    for i, c in enumerate(win_sorted):
        pos_ranks[pos][c["owner_id"]]["win_rank"] = i + 1
        pos_ranks[pos][c["owner_id"]]["starter_winnow"] = c["pos_totals"][pos]["starter_winnow"]

for c in construction:
    win_now_idx = pct_rank(all_starters_winnow, c["starters_winnow"] or 0)
    rebuild_idx = pct_rank(all_young_dyn, c["young_dyn_sum"])
    overall_idx = pct_rank(all_dyn_total, c["dynasty_total"] or 0)

    # Posture classification
    if win_now_idx >= 70 and rebuild_idx >= 65:
        posture = "Super-Team"
        posture_tag = "superteam"
    elif win_now_idx >= 65:
        posture = "Contender"
        posture_tag = "contender"
    elif rebuild_idx >= 70 and win_now_idx < 55:
        posture = "Rebuilder"
        posture_tag = "rebuilder"
    elif win_now_idx < 40 and rebuild_idx < 40:
        posture = "Stuck in the Middle"
        posture_tag = "stuck"
    elif rebuild_idx >= 55 and win_now_idx < 50:
        posture = "Young & Building"
        posture_tag = "building"
    else:
        posture = "Balanced"
        posture_tag = "balanced"

    # Strengths / weaknesses among fantasy-relevant positions
    offensive = ["QB", "RB", "WR", "TE"]
    strengths = [pos for pos in offensive if pos_ranks[pos][c["owner_id"]]["dyn_rank"] <= 3]
    weaknesses = [pos for pos in offensive if pos_ranks[pos][c["owner_id"]]["dyn_rank"] >= 8]

    # One-line recommendation
    if posture_tag == "superteam":
        rec = "You're the team to beat. Keep win-now pieces; only trade prospects for immediate starters."
    elif posture_tag == "contender":
        rec = "Push now — trade future picks for proven starters, especially at " + (", ".join(weaknesses) if weaknesses else "depth") + "."
    elif posture_tag == "rebuilder":
        rec = "Rebuild mode — sell aging vets for future picks and young upside. Target " + (", ".join(weaknesses) if weaknesses else "premium positions") + "."
    elif posture_tag == "stuck":
        rec = "Pick a lane. Either trade aging starters for picks or consolidate youth for a real starter."
    elif posture_tag == "building":
        rec = "Stockpile and be patient. You have youth; now add another 1–2 starters before pushing."
    else:
        rec = "Balanced roster — make marginal moves at " + (", ".join(weaknesses) if weaknesses else "weak spots") + " to tilt contender."

    c.update({
        "win_now_index": win_now_idx,
        "rebuild_index": rebuild_idx,
        "overall_index": overall_idx,
        "posture": posture,
        "posture_tag": posture_tag,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendation": rec,
        "pos_ranks": {pos: pos_ranks[pos][c["owner_id"]] for pos in ["QB", "RB", "WR", "TE", "K", "DEF", "DL", "LB", "DB"]},
    })

# sort construction by win_now_index descending for default display
construction.sort(key=lambda c: c["win_now_index"], reverse=True)

# ────────────────────────────────────────────────────────────────────────────
# Feature 3: Future draft pick ownership
# ────────────────────────────────────────────────────────────────────────────
print(f"[4/5] Resolving future pick ownership")

# Load traded picks scoped to current league
with open(TRADED_PICKS_CSV) as f:
    traded = list(csv.DictReader(f))
# filter: only current league, future seasons
traded_current = [t for t in traded if t["_league_id"] == CURRENT_LEAGUE_ID]

# roster_id -> owner_id mapping from teams
rid_to_ownerid = {t["roster_id"]: t["owner_id"] for t in teams}
rid_to_owner = {t["roster_id"]: t for t in teams}

# Build a lookup of (season, round, original_roster_id) -> current_owner_roster_id
# Sleeper's traded_picks table has one row per (season, round, original_owner) with current owner
override = {}
for t in traded_current:
    season = int(t["season"])
    rnd = int(t["round"])
    prev = int(t["previous_owner_id"])
    now = int(t["owner_id"])
    key = (season, rnd, prev)
    override[key] = now

# FantasyCalc pick values lookup — map "2026 Pick 1.XX" or similar to a rough value
# For Huddlepuffers we don't know draft order yet, so we'll show "early/mid/late" value estimates
# by looking at typical values. Strategy: take the median dyn value for R1, R2, etc in FantasyCalc.
pick_value_by_round = {}
for pick in picks:
    name = pick.get("full_name", "")
    # Parse "2026 Pick 1.XX" or "2026 Mid 1st"
    # FantasyCalc usually provides "2026 Early 1st", "2026 Mid 1st", "2026 Late 1st"
    round_val = None
    for r in range(1, 6):
        if f"{r}.0" in name or f"{r}st" in name or f" {r}nd" in name or f" {r}rd" in name or f"Pick {r}." in name:
            round_val = r
            break
    if round_val:
        pick_value_by_round.setdefault(round_val, []).append(pick.get("trade_dyn_value") or 0)

round_median = {}
for r, vals in pick_value_by_round.items():
    if vals:
        vals_sorted = sorted(vals)
        round_median[r] = vals_sorted[len(vals_sorted) // 2]

# Build the pick inventory
# For each (season, round, original_roster_id), the current owner is override or original
owned_picks = defaultdict(list)  # owner_roster_id -> list of pick dicts
for season in FUTURE_SEASONS:
    for rnd in range(1, ROOKIE_DRAFT_ROUNDS + 1):
        for original_rid in range(1, 11):
            current_rid = override.get((season, rnd, original_rid), original_rid)
            original_team = rid_to_owner.get(str(original_rid), {})
            current_team = rid_to_owner.get(str(current_rid), {})
            pick_entry = {
                "season": season,
                "round": rnd,
                "original_roster_id": original_rid,
                "original_owner_name": original_team.get("owner_name", f"r{original_rid}"),
                "current_roster_id": current_rid,
                "current_owner_name": current_team.get("owner_name", f"r{current_rid}"),
                "is_traded": override.get((season, rnd, original_rid)) is not None,
                "estimated_value": round_median.get(rnd, 0),
                # Original team record — lower wins = better pick slot
                "original_record_wins": original_team.get("wins"),
                "original_record_losses": original_team.get("losses"),
            }
            owned_picks[current_rid].append(pick_entry)

# Build matrix rows (one per team, columns = years × rounds, values = count of picks)
pick_matrix = []
pick_totals = []  # for the pick-rich / pick-poor leaderboard
for t in sorted(teams, key=lambda x: int(x["roster_id"])):
    rid = int(t["roster_id"])
    my_picks = owned_picks.get(rid, [])
    row = {
        "roster_id": rid,
        "owner_id": t["owner_id"],
        "owner_name": t["owner_name"],
        "is_me": t["owner_id"] == MY_USER_ID,
        "total_picks": len(my_picks),
        "total_value": sum(p["estimated_value"] for p in my_picks),
        "picks": my_picks,
    }
    # column counts: e.g. "2026_R1": 1
    for season in FUTURE_SEASONS:
        for rnd in range(1, ROOKIE_DRAFT_ROUNDS + 1):
            row[f"{season}_R{rnd}"] = sum(1 for p in my_picks if p["season"] == season and p["round"] == rnd)
    pick_matrix.append(row)
    pick_totals.append({
        "roster_id": rid,
        "owner_name": t["owner_name"],
        "is_me": t["owner_id"] == MY_USER_ID,
        "total_picks": row["total_picks"],
        "total_value": row["total_value"],
    })

pick_totals.sort(key=lambda x: (-x["total_value"], -x["total_picks"]))

# ────────────────────────────────────────────────────────────────────────────
# Write augmented JSON
# ────────────────────────────────────────────────────────────────────────────
print(f"[5/5] Writing {OUTPUT_JSON}")

data["extras"] = {
    "generated_at": datetime.utcnow().isoformat() + "Z",
    "history": {
        "snapshot_dates": sorted(set(snapshot_dates)),
        "by_player": {k: v for k, v in history.items()},
    },
    "risers_fallers": risers_fallers,
    "construction": construction,
    "future_picks": {
        "matrix": pick_matrix,
        "totals": pick_totals,
        "seasons": FUTURE_SEASONS,
        "rounds": list(range(1, ROOKIE_DRAFT_ROUNDS + 1)),
    },
}

# Also clean up trend_30day NaN values in the base players array
for p in data["players"]:
    p["trend_30day"] = clean_num(p.get("trend_30day"))

with open(OUTPUT_JSON, "w") as f:
    json.dump(data, f, default=str)

size = os.path.getsize(OUTPUT_JSON)
print(f"      wrote {size:,} bytes")
print(f"\n=== SUMMARY ===")
print(f"Snapshots:      {len(snapshot_dates)}")
print(f"Players w/hist: {len(history)}")
print(f"Risers:         {len(risers_fallers['risers'])}, Fallers: {len(risers_fallers['fallers'])}")
print(f"Teams scored:   {len(construction)}")
print(f"Future picks:   {sum(len(p['picks']) for p in pick_matrix)} total across {len(pick_matrix)} teams")
print(f"\nPosture breakdown:")
from collections import Counter
for p, n in Counter(c["posture"] for c in construction).most_common():
    print(f"  {p}: {n}")
print(f"\nNick (roster 5) summary:")
me_c = next((c for c in construction if c["owner_id"] == MY_USER_ID), None)
if me_c:
    print(f"  Posture: {me_c['posture']}")
    print(f"  Win-Now: {me_c['win_now_index']}  Rebuild: {me_c['rebuild_index']}  Overall: {me_c['overall_index']}")
    print(f"  Avg starter age: {me_c['avg_starter_age']}")
    print(f"  Strengths: {me_c['strengths']}  Weaknesses: {me_c['weaknesses']}")
    print(f"  Rec: {me_c['recommendation']}")
me_picks = next((p for p in pick_matrix if p["roster_id"] == 5), None)
if me_picks:
    print(f"  Future picks: {me_picks['total_picks']} total (value={me_picks['total_value']})")
    for pk in me_picks["picks"]:
        mark = "(original)" if not pk["is_traded"] else f"(via trade, originally {pk['original_owner_name']})"
        print(f"    {pk['season']} R{pk['round']} {mark}")
