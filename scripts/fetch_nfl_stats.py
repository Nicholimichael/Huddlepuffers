"""
fetch_nfl_stats.py — Pull weekly NFL player stats and advanced metrics via nfl-data-py.

Loads seasons ONE AT A TIME and concatenates successful ones, so a missing
season (e.g., 2025 not yet published) doesn't kill the whole pull.

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
from pathlib import Path
import pandas as pd
import nfl_data_py as nfl

# ---------- CONFIG ----------
SEASONS = list(range(2019, 2026))        # 2025 may 404 if not yet released — we handle it
# ----------------------------

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "csv"
DB_PATH = ROOT / "db" / "fantasy.sqlite"
CSV.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


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


def pull_by_season(importer, label, conn, out_name, seasons=SEASONS):
    """Call importer(year=[y]) for each year individually, concat successes."""
    print(f"\n[{label}] Per-season pull")
    frames = []
    ok = []
    for y in seasons:
        try:
            df = importer([y])
            if df is not None and not df.empty:
                frames.append(df)
                ok.append(y)
                print(f"  {y}: {len(df):,} rows")
            else:
                print(f"  {y}: empty")
        except Exception as e:
            print(f"  {y}: FAILED ({type(e).__name__}: {str(e)[:80]})")
    if frames:
        combined = pd.concat(frames, ignore_index=True)
        write(combined, out_name, conn)
        print(f"  [{label}] total: {len(combined):,} rows across seasons {ok}")
    else:
        print(f"  [{label}] no seasons succeeded")


def main():
    conn = sqlite3.connect(DB_PATH)
    print(f"Target seasons: {SEASONS}")

    pull_by_season(nfl.import_weekly_data, "1/6 Weekly stats", conn, "nfl_weekly_stats")
    pull_by_season(nfl.import_seasonal_data, "2/6 Seasonal stats", conn, "nfl_seasonal_stats")
    pull_by_season(nfl.import_seasonal_rosters, "3/6 Rosters", conn, "nfl_rosters")

    print("\n[4/6 Player ID crosswalk]")
    try:
        ids = nfl.import_ids()
        write(ids, "nfl_player_ids", conn)
    except Exception as e:
        print(f"  FAILED: {e}")

    pull_by_season(nfl.import_snap_counts, "5/6 Snap counts", conn, "nfl_snap_counts")

    print("\n[6/6 Next Gen Stats]")
    for stat_type in ("passing", "rushing", "receiving"):
        print(f"  -- {stat_type} --")
        frames = []
        ok = []
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
    # so indexes must be (re)created after the loads complete. Composite indexes
    # cover the (season, season_type, week) and (season, week) filters used by
    # build_rankings.py and build_extras_v3.py.
    print("\n=== Building indexes ===")
    cur = conn.cursor()
    INDEXES = [
        ("idx_nfl_weekly_stats_season_type_week",
         "nfl_weekly_stats", "(season, season_type, week)"),
        ("idx_nfl_snap_counts_season_week",
         "nfl_snap_counts",  "(season, week)"),
    ]
    for name, table, cols in INDEXES:
        # Only create if the table actually exists (a failed pull may have skipped it).
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
    for t in sorted([r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'nfl_%'")]):
        n = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        print(f"  {t}: {n:,} rows")

    conn.commit()
    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
