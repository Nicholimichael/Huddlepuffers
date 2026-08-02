"""
fetch_nfl_stats.py — Pull weekly NFL player stats and advanced metrics.

2026-08-02 (v3): nfl-data-py's weekly/seasonal endpoints went stale — nflverse
moved player stats to the `stats_player` release (the old `player_stats` release
stops at 2024, which silently froze this dashboard's PPG/target-share numbers on
the 2024 season). Weekly + seasonal pulls now go straight to the nflverse
release assets, with nfl-data-py kept as a per-season fallback:

  weekly  : stats_player/stats_player_week_{year}.parquet   (falls back to nfl.import_weekly_data)
  seasonal: stats_player/stats_player_reg_{year}.parquet    (falls back to nfl.import_seasonal_data,
            then to aggregating the weekly frame)

Seasons are derived from config.CURRENT_SEASON — never hardcoded — so a league
rollover can't truncate the pull again. Loads seasons ONE AT A TIME and
concatenates successful ones, so a missing season (e.g., the current season
before games start) doesn't kill the whole pull. If the most recent COMPLETED
season is missing from the weekly results, a ::warning:: annotation is emitted
so the staleness is visible in the Actions run instead of buried in a log line.

Outputs:
  - data/csv/nfl_weekly_stats.csv       : per-player per-week stats
  - data/csv/nfl_seasonal_stats.csv     : per-player per-season stats
  - data/csv/nfl_rosters.csv            : NFL rosters (cross-reference via gsis_id)
  - data/csv/nfl_player_ids.csv         : ID crosswalk (sleeper <-> gsis <-> pfr ...)
  - data/csv/nfl_snap_counts.csv        : snap counts by week
  - data/csv/nfl_ngs_*.csv              : Next Gen Stats

Usage:
    python3 fetch_nfl_stats.py
"""

import sqlite3
import sys
from pathlib import Path
import pandas as pd
import nfl_data_py as nfl

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import config  # noqa: E402

# ---------- CONFIG ----------
FIRST_SEASON = 2019
SEASONS = list(range(FIRST_SEASON, config.CURRENT_SEASON + 1))
NFLVERSE = "https://github.com/nflverse/nflverse-data/releases/download"
# ----------------------------

CSV = ROOT / "data" / "csv"
DB_PATH = ROOT / "db" / "fantasy.sqlite"
CSV.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Columns downstream consumers (build_rankings.py / build_extras_v3.py /
# weekly_digest.py) actually query. A pull that can't provide these is a
# failed pull, not a schema drift we paper over.
WEEKLY_REQUIRED = {"player_id", "season", "week", "season_type",
                   "fantasy_points_ppr", "target_share", "targets",
                   "carries", "receptions", "opponent_team"}
SEASONAL_REQUIRED = {"player_id", "season", "season_type", "games",
                     "fantasy_points_ppr", "target_share", "targets",
                     "carries", "receptions"}

# Known nflverse column renames across the player_stats -> stats_player move.
RENAMES = {
    "player_gsis_id": "player_id",
    "gsis_id": "player_id",
    "recent_team": "team",
    "opponent": "opponent_team",
}


def _harmonize(df, required, label, year):
    df = df.rename(columns={k: v for k, v in RENAMES.items() if k in df.columns})
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{label} {year}: nflverse asset missing columns {sorted(missing)}")
    return df


def nflverse_weekly(years):
    y = years[0]
    df = pd.read_parquet(f"{NFLVERSE}/stats_player/stats_player_week_{y}.parquet")
    return _harmonize(df, WEEKLY_REQUIRED, "weekly", y)


def nflverse_seasonal(years):
    y = years[0]
    df = pd.read_parquet(f"{NFLVERSE}/stats_player/stats_player_reg_{y}.parquet")
    if "season_type" not in df.columns:
        df["season_type"] = "REG"
    if "games" not in df.columns and "games_played" in df.columns:
        df = df.rename(columns={"games_played": "games"})
    return _harmonize(df, SEASONAL_REQUIRED, "seasonal", y)


def seasonal_from_weekly(weekly_df, year):
    """Last-resort seasonal aggregate built from the weekly frame."""
    wk = weekly_df[(weekly_df["season"] == year) & (weekly_df["season_type"] == "REG")]
    if wk.empty:
        return None
    agg = wk.groupby("player_id").agg(
        games=("week", "nunique"),
        fantasy_points_ppr=("fantasy_points_ppr", "sum"),
        target_share=("target_share", "mean"),
        targets=("targets", "sum"),
        carries=("carries", "sum"),
        receptions=("receptions", "sum"),
    ).reset_index()
    agg["season"] = year
    agg["season_type"] = "REG"
    return agg


def write(df, name, conn):
    if df is None or df.empty:
        print(f"  {name}: 0 rows (skipped)")
        return
    # JSON-safe: some columns may contain lists/dicts
    df = df.copy()
    for col in df.columns:
        sample = df[col].dropna()
        if len(sample) and isinstance(sample.iloc[0], (list, dict)):
            df[col] = df[col].astype(str)
    df.to_csv(CSV / f"{name}.csv", index=False)
    try:
        df.to_sql(name, conn, if_exists="replace", index=False)
        print(f"  {name}: {len(df):,} rows -> csv + db")
    except Exception as e:
        print(f"  {name}: CSV written but DB write failed: {e}")


def pull_by_season(importers, label, conn, out_name, seasons=SEASONS):
    """Try each importer in order per season; concat successes across seasons.

    `importers` is a list of (name, fn) — fn takes [year] and returns a frame.
    Returns (combined_frame_or_None, ok_years).
    """
    print(f"\n[{label}] Per-season pull")
    frames, ok = [], []
    for y in seasons:
        got = None
        errs = []
        for src_name, fn in importers:
            try:
                df = fn([y])
                if df is not None and not df.empty:
                    got = df
                    print(f"  {y}: {len(df):,} rows ({src_name})")
                    break
                errs.append(f"{src_name}: empty")
            except Exception as e:
                errs.append(f"{src_name}: {type(e).__name__}: {str(e)[:70]}")
        if got is not None:
            frames.append(got)
            ok.append(y)
        else:
            print(f"  {y}: FAILED ({' | '.join(errs)})")
    combined = None
    if frames:
        combined = pd.concat(frames, ignore_index=True)
        write(combined, out_name, conn)
        print(f"  [{label}] total: {len(combined):,} rows across seasons {ok}")
    else:
        print(f"  [{label}] no seasons succeeded")
    return combined, ok


def main():
    conn = sqlite3.connect(DB_PATH)
    print(f"Target seasons: {SEASONS} (derived from config.CURRENT_SEASON={config.CURRENT_SEASON})")

    weekly_df, weekly_ok = pull_by_season(
        [("nflverse", nflverse_weekly), ("nfl-data-py", nfl.import_weekly_data)],
        "1/6 Weekly stats", conn, "nfl_weekly_stats")

    seasonal_importers = [("nflverse", nflverse_seasonal),
                          ("nfl-data-py", nfl.import_seasonal_data)]
    if weekly_df is not None:
        seasonal_importers.append(
            ("weekly-aggregate", lambda ys: seasonal_from_weekly(weekly_df, ys[0])))
    pull_by_season(seasonal_importers, "2/6 Seasonal stats", conn, "nfl_seasonal_stats")

    # Staleness tripwire: the most recent COMPLETED season must be in the weekly
    # pull. (The in-progress/upcoming season legitimately may not exist yet.)
    last_complete = config.LAST_COMPLETE_SEASON
    if last_complete not in weekly_ok:
        print(f"::warning::[fetch_nfl_stats] weekly stats for the completed "
              f"{last_complete} season are MISSING — PPG/target-share views are "
              f"anchored to {max(weekly_ok) if weekly_ok else 'nothing'}. "
              f"Check the nflverse asset URLs.")

    pull_by_season([("nfl-data-py", nfl.import_seasonal_rosters)],
                   "3/6 Rosters", conn, "nfl_rosters")

    print("\n[4/6 Player ID crosswalk]")
    try:
        ids = nfl.import_ids()
        write(ids, "nfl_player_ids", conn)
    except Exception as e:
        print(f"  FAILED: {e}")

    pull_by_season([("nfl-data-py", nfl.import_snap_counts)],
                   "5/6 Snap counts", conn, "nfl_snap_counts")

    print("\n[6/6 Next Gen Stats]")
    for stat_type in ("passing", "rushing", "receiving"):
        print(f"  -- {stat_type} --")
        frames, ok = [], []
        for y in SEASONS:
            try:
                df = nfl.import_ngs_data(stat_type=stat_type, years=[y])
                if df is not None and not df.empty:
                    frames.append(df)
                    ok.append(y)
            except Exception as e:
                print(f"    {y}: FAILED ({str(e)[:60]})")
        if frames:
            write(pd.concat(frames, ignore_index=True), f"nfl_ngs_{stat_type}", conn)
            print(f"    seasons ok: {ok}")

    # Indexes — `to_sql(if_exists="replace")` drops the table on every refresh,
    # so indexes must be (re)created after the loads complete.
    print("\n=== Building indexes ===")
    cur = conn.cursor()
    INDEXES = [
        ("idx_nfl_weekly_stats_season_type_week",
         "nfl_weekly_stats", "(season, season_type, week)"),
        ("idx_nfl_snap_counts_season_week",
         "nfl_snap_counts",  "(season, week)"),
    ]
    for name, table, cols in INDEXES:
        exists = cur.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        if exists:
            cur.execute(f'CREATE INDEX IF NOT EXISTS {name} ON "{table}" {cols}')
            print(f"  {name} on {table}{cols}")
        else:
            print(f"  {table}: missing — skipped index {name}")

    # Summary
    print("\n=== Summary ===")
    for t in sorted([r[0] for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'nfl_%'")]):
        n = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        print(f"  {t}: {n:,} rows")

    conn.commit()
    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
