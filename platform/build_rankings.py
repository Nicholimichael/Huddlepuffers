"""Build composite dynasty + win-now rankings JSON for the Huddlepuffers interactive platform."""
import sqlite3, json, pandas as pd, numpy as np, os
from datetime import datetime
from pathlib import Path

# Path flexibility: works locally on macOS and inside the Cowork Linux sandbox.
HERE = Path(__file__).resolve().parent           # .../Fantasy Football/platform
PROJECT = HERE.parent                            # .../Fantasy Football
DB = str(PROJECT / "db" / "fantasy.sqlite")
OUTPUT_JSON = str(HERE / "rankings_data.json")

con = sqlite3.connect(DB)
LATEST_NFL_SEASON = int(pd.read_sql("SELECT MAX(season) AS s FROM nfl_weekly_stats", con).iloc[0, 0])
ACTIVE_LEAGUE = pd.read_sql("SELECT league_id FROM leagues WHERE season='2025'", con).iloc[0, 0]
MY_USER_ID = "472596585608376320"  # Nmhochstedler

# Users (one row per unique user across all seasons, keep most recent display name)
# Join to leagues so we can order by season DESC and pick the latest known name.
users = pd.read_sql(
    "SELECT u.user_id, u.display_name, l.season "
    "FROM users u LEFT JOIN leagues l ON l.league_id = u.league_id "
    "ORDER BY l.season DESC",
    con,
).drop_duplicates("user_id", keep="first")[["user_id", "display_name"]]

# Rosters for active league
rosters = pd.read_sql(
    f"SELECT roster_id, owner_id, wins, losses, fpts, fpts_against, ppts FROM rosters WHERE league_id='{ACTIVE_LEAGUE}'", con
)
rosters = rosters.merge(users, left_on="owner_id", right_on="user_id", how="left")

# Player -> owner
rp = pd.read_sql(
    f"SELECT player_id, owner_id, roster_id, is_starter, is_taxi, is_reserve "
    f"FROM roster_players WHERE league_id='{ACTIVE_LEAGUE}'", con,
)
rp = rp.merge(users, left_on="owner_id", right_on="user_id", how="left")

# FantasyCalc
fc = pd.read_sql(
    "SELECT fantasycalc_id, sleeper_id, full_name, position, team, age, value AS fc_dyn, "
    "redraft_value AS fc_red, overall_rank AS fc_dyn_rank, redraft_rank AS fc_red_rank, "
    "position_rank AS fc_dyn_pos_rank, redraft_position_rank AS fc_red_pos_rank, trend_30day "
    "FROM fantasycalc_values", con,
)
picks = fc[fc["position"] == "PICK"].copy()
players_fc = fc[fc["position"] != "PICK"].copy()

# Sleeper master (active + rostered)
sp = pd.read_sql(
    "SELECT player_id, full_name, position, team, age, years_exp, status, injury_status, fantasy_positions "
    "FROM players", con,
)

ids = pd.read_sql("SELECT sleeper_id, gsis_id, pfr_id, name FROM nfl_player_ids", con)

# Season & recent stats
seas = pd.read_sql(
    f"SELECT player_id AS gsis_id, games, fantasy_points_ppr, target_share, carries, targets, receptions "
    f"FROM nfl_seasonal_stats WHERE season={LATEST_NFL_SEASON} AND season_type='REG'", con,
)

max_week = int(pd.read_sql(
    f"SELECT MAX(week) AS w FROM nfl_weekly_stats WHERE season={LATEST_NFL_SEASON} AND season_type='REG'", con
).iloc[0, 0])
last_n = 8
start_wk = max(1, max_week - last_n + 1)
recent = pd.read_sql(
    f"SELECT player_id AS gsis_id, AVG(fantasy_points_ppr) AS recent_ppg, "
    f"AVG(target_share) AS recent_tgt_share, COUNT(*) AS recent_games "
    f"FROM nfl_weekly_stats WHERE season={LATEST_NFL_SEASON} AND season_type='REG' AND week >= {start_wk} "
    f"GROUP BY player_id", con,
)
snap = pd.read_sql(
    f"SELECT pfr_player_id AS pfr_id, AVG(offense_pct) AS recent_off_snap_pct, "
    f"AVG(defense_pct) AS recent_def_snap_pct "
    f"FROM nfl_snap_counts WHERE season={LATEST_NFL_SEASON} AND week >= {start_wk} "
    f"GROUP BY pfr_player_id", con,
)

# Normalize IDs as strings
for df in (rp, players_fc, sp, ids, picks):
    if "sleeper_id" in df.columns:
        df["sleeper_id"] = df["sleeper_id"].astype(str)
    if "player_id" in df.columns:
        df["player_id"] = df["player_id"].astype(str)

rostered_ids = set(rp["player_id"].unique())
universe_ids = rostered_ids | set(players_fc["sleeper_id"].dropna().astype(str).unique())

base = sp[sp["player_id"].isin(universe_ids)].copy()
missing = universe_ids - set(base["player_id"])
if missing:
    in_list = ",".join(repr(x) for x in missing)
    extra = pd.read_sql(
        f"SELECT player_id, full_name, position, team, age, years_exp, status, injury_status, fantasy_positions "
        f"FROM players WHERE player_id IN ({in_list})", con,
    )
    base = pd.concat([base, extra], ignore_index=True).drop_duplicates("player_id")

base = base.merge(
    players_fc[["sleeper_id", "fc_dyn", "fc_red", "fc_dyn_rank", "fc_red_rank",
                "fc_dyn_pos_rank", "fc_red_pos_rank", "trend_30day"]],
    left_on="player_id", right_on="sleeper_id", how="left",
)
base = base.merge(ids[["sleeper_id", "gsis_id", "pfr_id"]],
                  left_on="player_id", right_on="sleeper_id", how="left", suffixes=("", "_ids"))
base = base.merge(seas, on="gsis_id", how="left")
base = base.merge(recent, on="gsis_id", how="left")
base = base.merge(snap, on="pfr_id", how="left")

rp_short = rp[["player_id", "owner_id", "display_name", "is_starter", "is_taxi", "is_reserve"]].rename(
    columns={"display_name": "owner_name"}
)
base = base.merge(rp_short, on="player_id", how="left")
base["rostered"] = base["owner_id"].notna()


def norm(s):
    s = pd.to_numeric(s, errors="coerce")
    lo = s.quantile(0.02)
    hi = s.quantile(0.98)
    if pd.isna(hi) or pd.isna(lo) or hi == lo:
        return pd.Series(50.0, index=s.index)
    return ((s - lo) / (hi - lo) * 100).clip(0, 100)


AGE_PEAK = {"QB": 31, "RB": 24, "WR": 26, "TE": 27, "K": 28, "DEF": 28}
AGE_HALFLIFE = {"QB": 6, "RB": 3.5, "WR": 5, "TE": 5, "K": 6, "DEF": 6}


def age_dynasty_mult(row):
    pos = row["position"]
    age = row["age"]
    if pd.isna(age) or pos not in AGE_PEAK:
        return 1.0
    peak = AGE_PEAK[pos]
    hl = AGE_HALFLIFE[pos]
    if age <= peak:
        return 1.0 + max(0, (peak - age) * 0.04)
    delta = age - peak
    return max(0.35, 0.5 ** (delta / hl) + 0.5)


base["age_mult"] = base.apply(age_dynasty_mult, axis=1)

for c in ["fantasy_points_ppr", "recent_ppg", "target_share", "recent_tgt_share", "recent_off_snap_pct"]:
    base[c] = pd.to_numeric(base[c], errors="coerce").fillna(0)
base["fc_dyn"] = pd.to_numeric(base["fc_dyn"], errors="coerce").fillna(0)
base["fc_red"] = pd.to_numeric(base["fc_red"], errors="coerce").fillna(0)

base["n_fc_dyn"] = base.groupby("position")["fc_dyn"].transform(norm)
base["n_fc_red"] = base.groupby("position")["fc_red"].transform(norm)
base["season_ppg"] = base["fantasy_points_ppr"] / base["games"].replace(0, np.nan)
base["n_season_ppg"] = base.groupby("position")["season_ppg"].transform(norm).fillna(0)
base["n_recent_ppg"] = base.groupby("position")["recent_ppg"].transform(norm).fillna(0)
base["n_snap"] = base.groupby("position")["recent_off_snap_pct"].transform(norm).fillna(0)
base["n_tgt_share"] = base.groupby("position")["recent_tgt_share"].transform(norm).fillna(0)

# --- Dynasty score: 65% FC dynasty, 20% age-adjusted FC, 15% recent production ---
base["dynasty_score_raw"] = (
    0.65 * base["n_fc_dyn"]
    + 0.20 * (base["n_fc_dyn"] * base["age_mult"]).clip(0, 100)
    + 0.15 * base["n_recent_ppg"]
)
youth_mask = (base["age"] <= 23) & (base["n_fc_dyn"] > 50)
base.loc[youth_mask, "dynasty_score_raw"] += 3

# --- Win Now score: 55% FC redraft + 25% last-8 PPG + 10% snap + 10% target share ---
base["winnow_score_raw"] = (
    0.55 * base["n_fc_red"]
    + 0.25 * base["n_recent_ppg"]
    + 0.10 * base["n_snap"]
    + 0.10 * base["n_tgt_share"]
)

base["dynasty_score"] = base["dynasty_score_raw"].clip(0, 100).round(1)
base["winnow_score"] = base["winnow_score_raw"].clip(0, 100).round(1)

base["dynasty_pos_rank"] = base.groupby("position")["dynasty_score"].rank(method="min", ascending=False)
base["winnow_pos_rank"] = base.groupby("position")["winnow_score"].rank(method="min", ascending=False)
base["dynasty_overall_rank"] = base["dynasty_score"].rank(method="min", ascending=False)
base["winnow_overall_rank"] = base["winnow_score"].rank(method="min", ascending=False)


def impute_value(row, kind):
    if kind == "dyn":
        if row["fc_dyn"] > 0:
            return float(row["fc_dyn"])
        return max(25.0, float(row["dynasty_score"]) * 80.0)
    if row["fc_red"] > 0:
        return float(row["fc_red"])
    return max(25.0, float(row["winnow_score"]) * 80.0)


base["trade_dyn_value"] = base.apply(lambda r: impute_value(r, "dyn"), axis=1)
base["trade_red_value"] = base.apply(lambda r: impute_value(r, "red"), axis=1)

keep_cols = [
    "player_id", "full_name", "position", "team", "age", "years_exp", "status", "injury_status",
    "owner_id", "owner_name", "is_starter", "is_taxi", "is_reserve", "rostered",
    "fc_dyn", "fc_red", "fc_dyn_rank", "fc_red_rank", "trend_30day",
    "games", "fantasy_points_ppr", "season_ppg", "target_share",
    "recent_ppg", "recent_tgt_share", "recent_off_snap_pct",
    "dynasty_score", "winnow_score", "dynasty_pos_rank", "winnow_pos_rank",
    "dynasty_overall_rank", "winnow_overall_rank", "trade_dyn_value", "trade_red_value", "age_mult",
]
players_out = base[keep_cols].copy()

# Round numeric for smaller JSON
for c in ["dynasty_score", "winnow_score", "age_mult", "recent_ppg", "recent_tgt_share",
          "recent_off_snap_pct", "season_ppg", "trade_dyn_value", "trade_red_value", "target_share",
          "fantasy_points_ppr"]:
    players_out[c] = pd.to_numeric(players_out[c], errors="coerce").round(2)

for c in ["dynasty_pos_rank", "winnow_pos_rank", "dynasty_overall_rank", "winnow_overall_rank",
          "games", "is_starter", "is_taxi", "is_reserve", "years_exp", "fc_dyn_rank", "fc_red_rank"]:
    players_out[c] = pd.to_numeric(players_out[c], errors="coerce")

players_out = players_out.where(pd.notnull(players_out), None)

# Picks (note: picks came from `fc` after column rename, so it has fc_dyn/fc_red not value/redraft_value)
picks_out = picks[["fantasycalc_id", "full_name", "fc_dyn", "fc_red", "fc_dyn_rank"]].copy()
picks_out = picks_out.rename(columns={"fc_dyn": "trade_dyn_value", "fc_red": "trade_red_value", "fc_dyn_rank": "overall_rank"})
picks_out["position"] = "PICK"
picks_out["player_id"] = "PICK_" + picks_out["fantasycalc_id"].astype(str)
# Sort by dynasty value desc
picks_out = picks_out.sort_values("trade_dyn_value", ascending=False)
picks_out = picks_out.where(pd.notnull(picks_out), None)

# Teams
teams = rosters.rename(columns={"display_name": "owner_name"})
teams = teams[["roster_id", "owner_id", "owner_name", "wins", "losses", "fpts", "fpts_against", "ppts"]].copy()
rv = (
    base[base["rostered"] == True]
    .groupby("owner_id")
    .agg(
        dynasty_total=("dynasty_score", "sum"),
        winnow_total=("winnow_score", "sum"),
        roster_size=("player_id", "count"),
    ).reset_index()
)
starters_val = (
    base[(base["rostered"] == True) & (base["is_starter"] == 1)]
    .groupby("owner_id")
    .agg(
        starters_winnow=("winnow_score", "sum"),
        starters_dynasty=("dynasty_score", "sum"),
    ).reset_index()
)
teams = teams.merge(rv, on="owner_id", how="left").merge(starters_val, on="owner_id", how="left")
teams["is_me"] = teams["owner_id"] == MY_USER_ID
for c in ["dynasty_total", "winnow_total", "starters_winnow", "starters_dynasty"]:
    teams[c] = pd.to_numeric(teams[c], errors="coerce").round(1)

# Write JSON
out = {
    "meta": {
        "league_id": str(ACTIVE_LEAGUE),
        "league_name": "The Huddlepuffers",
        "season": "2025",
        "my_user_id": MY_USER_ID,
        "my_display_name": "Nmhochstedler",
        "latest_nfl_season": LATEST_NFL_SEASON,
        "latest_nfl_week": max_week,
        "recent_window_weeks": last_n,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "ranking_methodology": {
            "dynasty": "65% FantasyCalc dynasty value + 20% age-adjusted value + 15% recent 8-week PPG (position-normalized). Youth bonus (+3) for age<=23 with FC value > 50.",
            "winnow": "55% FantasyCalc redraft value + 25% last-8-week PPG + 10% offensive snap share + 10% target share (position-normalized).",
        },
    },
    "teams": teams.where(pd.notnull(teams), None).to_dict(orient="records"),
    "players": players_out.to_dict(orient="records"),
    "picks": picks_out.to_dict(orient="records"),
}

with open(OUTPUT_JSON, "w") as f:
    json.dump(out, f, default=str)

print(f"wrote {OUTPUT_JSON}")
print(f"players: {len(out['players'])}, picks: {len(out['picks'])}, teams: {len(out['teams'])}")

# Sanity checks
pdf = pd.DataFrame(out["players"])
print("\n=== Top 20 Dynasty ===")
print(pdf.sort_values("dynasty_score", ascending=False)[
    ["full_name", "position", "team", "age", "dynasty_score", "winnow_score", "dynasty_pos_rank", "owner_name"]
].head(20).to_string(index=False))
print("\n=== Top 20 Win Now ===")
print(pdf.sort_values("winnow_score", ascending=False)[
    ["full_name", "position", "team", "age", "winnow_score", "dynasty_score", "winnow_pos_rank", "owner_name"]
].head(20).to_string(index=False))
print("\n=== My roster (Nmhochstedler) ===")
mine = pdf[pdf["owner_id"] == MY_USER_ID].sort_values("dynasty_score", ascending=False)
print(mine[["full_name", "position", "age", "dynasty_score", "winnow_score", "is_starter"]].to_string(index=False))
