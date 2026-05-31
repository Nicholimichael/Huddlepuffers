"""Build composite dynasty + win-now rankings JSON for the Huddlepuffers interactive platform."""
import sqlite3, json, pandas as pd, numpy as np, os, sys, re
from datetime import datetime
from pathlib import Path

# Make project-root config importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

DB = str(config.DB_PATH)
OUTPUT_JSON = str(config.PLATFORM_DIR / "rankings_data.json")

con = sqlite3.connect(DB)
LATEST_NFL_SEASON = int(pd.read_sql("SELECT MAX(season) AS s FROM nfl_weekly_stats", con).iloc[0, 0])
ACTIVE_LEAGUE = config.active_league_id_from_db(con)
MY_USER_ID = config.MY_USER_ID

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
    "SELECT roster_id, owner_id, wins, losses, fpts, fpts_against, ppts FROM rosters WHERE league_id = ?",
    con, params=[ACTIVE_LEAGUE],
)
rosters = rosters.merge(users, left_on="owner_id", right_on="user_id", how="left")

# Player -> owner
rp = pd.read_sql(
    "SELECT player_id, owner_id, roster_id, is_starter, is_taxi, is_reserve "
    "FROM roster_players WHERE league_id = ?",
    con, params=[ACTIVE_LEAGUE],
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

# KeepTradeCut — optional second market signal. Joined by normalized (name, position)
# because KTC's playersArray doesn't carry Sleeper IDs. If the table doesn't exist
# yet (first run before fetch_keeptradecut.py has been wired in), KTC_AVAILABLE
# stays False and the blend silently degrades to FC-only.
try:
    ktc = pd.read_sql(
        "SELECT full_name, position, ktc_dyn, ktc_red, "
        "ktc_dyn_rank, ktc_red_rank, ktc_dyn_pos_rank, ktc_red_pos_rank "
        "FROM ktc_values WHERE position != 'PICK'", con,
    )
    KTC_AVAILABLE = len(ktc) > 0
except Exception:
    ktc = pd.DataFrame()
    KTC_AVAILABLE = False
print(f"KTC available: {KTC_AVAILABLE} ({len(ktc)} rows)")

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

# Join KTC by normalized (name, position). KTC's array has no Sleeper ID, so we
# build a fuzzy-but-deterministic join key. Punctuation, suffixes (Jr/Sr/II/III/IV),
# and case all get stripped so "A.J. Brown" and "Aj Brown" collapse to the same key.
def _norm_name(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.lower()
    s = re.sub(r"[.\'`]", "", s)              # strip dots, apostrophes, backticks
    s = re.sub(r"\s+(jr|sr|ii|iii|iv|v)\b", "", s)  # strip generational suffixes
    s = re.sub(r"[^a-z0-9]+", " ", s)         # collapse other punctuation to space
    return s.strip()

if KTC_AVAILABLE:
    ktc = ktc.copy()
    ktc["_join_name"] = ktc["full_name"].map(_norm_name)
    ktc["_join_pos"] = ktc["position"].fillna("").str.upper()
    # Keep only the highest dynasty value per (name, pos) — KTC occasionally has
    # dupes for traded players still listed under the old team.
    ktc = ktc.sort_values("ktc_dyn", ascending=False).drop_duplicates(["_join_name", "_join_pos"])
    base["_join_name"] = base["full_name"].map(_norm_name)
    base["_join_pos"] = base["position"].fillna("").str.upper()
    base = base.merge(
        ktc[["_join_name", "_join_pos", "ktc_dyn", "ktc_red",
             "ktc_dyn_rank", "ktc_red_rank", "ktc_dyn_pos_rank", "ktc_red_pos_rank"]],
        on=["_join_name", "_join_pos"], how="left",
    )
    base = base.drop(columns=["_join_name", "_join_pos"])
    match_n = base["ktc_dyn"].notna().sum()
    print(f"KTC join: matched {match_n} / {len(base)} players ({100*match_n/len(base):.1f}%)")
else:
    for c in ["ktc_dyn", "ktc_red", "ktc_dyn_rank", "ktc_red_rank",
              "ktc_dyn_pos_rank", "ktc_red_pos_rank"]:
        base[c] = np.nan
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
base["ktc_dyn"] = pd.to_numeric(base["ktc_dyn"], errors="coerce")
base["ktc_red"] = pd.to_numeric(base["ktc_red"], errors="coerce")

# Position-normalized signals. FC and KTC live on different scales (FC tops out
# ~10000, KTC ~9999, but the floors and shapes differ), so normalize EACH source
# within its own position, then blend in normalized space.
base["n_fc_dyn"] = base.groupby("position")["fc_dyn"].transform(norm)
base["n_fc_red"] = base.groupby("position")["fc_red"].transform(norm)
# norm() of all-NaN returns 50; we want NaN-as-missing here so blending is fair.
def _norm_keep_nan(g):
    s = pd.to_numeric(g, errors="coerce")
    if s.notna().sum() < 5:
        return pd.Series(np.nan, index=s.index)
    return norm(s).where(s.notna(), np.nan)
base["n_ktc_dyn"] = base.groupby("position")["ktc_dyn"].transform(_norm_keep_nan)
base["n_ktc_red"] = base.groupby("position")["ktc_red"].transform(_norm_keep_nan)

# Blended market signal: 50/50 FC + KTC when both exist, else whichever does.
# Fallbacks preserve coverage for niche players one site rates and the other doesn't.
def _blend(a, b):
    return pd.concat([a, b], axis=1).mean(axis=1, skipna=True).fillna(0)
base["n_market_dyn"] = _blend(base["n_fc_dyn"], base["n_ktc_dyn"])
base["n_market_red"] = _blend(base["n_fc_red"], base["n_ktc_red"])

# Provenance flag — useful for the UI to label which signals fed each row.
base["market_sources"] = np.where(
    base["n_fc_dyn"].notna() & base["n_ktc_dyn"].notna(), "FC+KTC",
    np.where(base["n_fc_dyn"].notna(), "FC",
    np.where(base["n_ktc_dyn"].notna(), "KTC", "imputed"))
)

base["season_ppg"] = base["fantasy_points_ppr"] / base["games"].replace(0, np.nan)
base["n_season_ppg"] = base.groupby("position")["season_ppg"].transform(norm).fillna(0)
base["n_recent_ppg"] = base.groupby("position")["recent_ppg"].transform(norm).fillna(0)
base["n_snap"] = base.groupby("position")["recent_off_snap_pct"].transform(norm).fillna(0)
base["n_tgt_share"] = base.groupby("position")["recent_tgt_share"].transform(norm).fillna(0)

# --- Dynasty score: 65% blended market + 20% age-adjusted market + 15% recent production ---
base["dynasty_score_raw"] = (
    0.65 * base["n_market_dyn"]
    + 0.20 * (base["n_market_dyn"] * base["age_mult"]).clip(0, 100)
    + 0.15 * base["n_recent_ppg"]
)
youth_mask = (base["age"] <= 23) & (base["n_market_dyn"] > 50)
base.loc[youth_mask, "dynasty_score_raw"] += 3

# --- Win Now score: 55% blended market redraft + 25% last-8 PPG + 10% snap + 10% target share ---
base["winnow_score_raw"] = (
    0.55 * base["n_market_red"]
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
    "ktc_dyn", "ktc_red", "ktc_dyn_rank", "ktc_red_rank", "market_sources",
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
        "league_name": config.LEAGUE_DISPLAY_NAME,
        "season": config.CURRENT_SEASON_STR,
        "my_user_id": MY_USER_ID,
        "my_display_name": config.MY_DISPLAY_NAME,
        "latest_nfl_season": LATEST_NFL_SEASON,
        "latest_nfl_week": max_week,
        "recent_window_weeks": last_n,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "ktc_available": KTC_AVAILABLE,
        "ranking_methodology": {
            "dynasty": (
                "65% blended market dynasty value + 20% age-adjusted market value + "
                "15% recent 8-week PPG (position-normalized). "
                "Market value = 50/50 blend of FantasyCalc and KeepTradeCut when both exist, "
                "else whichever source has a value. Youth bonus (+3) for age<=23 with market value > 50."
            ),
            "winnow": (
                "55% blended market redraft value + 25% last-8-week PPG + "
                "10% offensive snap share + 10% target share (position-normalized). "
                "Market value blends FantasyCalc and KeepTradeCut as above."
            ),
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
print(f"\n=== My roster ({config.MY_DISPLAY_NAME}) ===")
mine = pdf[pdf["owner_id"] == MY_USER_ID].sort_values("dynasty_score", ascending=False)
print(mine[["full_name", "position", "age", "dynasty_score", "winnow_score", "is_starter"]].to_string(index=False))
