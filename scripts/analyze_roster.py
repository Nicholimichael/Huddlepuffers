"""
analyze_roster.py — Roster valuation + positional scorecard for Nick's Huddlepuffers team.

Ties together:
  - Current Sleeper roster (roster_players)
  - FantasyCalc dynasty values (fantasycalc_values)
  - NFL weekly stats (nfl_weekly_stats, if present)
  - Player metadata (players, nfl_player_ids)

Outputs:
  - data/csv/analysis_roster_value.csv     : your roster with value + rank + age + position rank
  - data/csv/analysis_league_valuation.csv : every team's total roster value (dynasty + picks)
  - data/csv/analysis_position_strength.csv: where you rank at each position
  - data/csv/analysis_age_risk.csv         : players 29+ with high value (sell window)
  - data/csv/analysis_buy_low.csv          : sub-25 players with rising 30-day trends
  - Prints an executive summary to console

Usage:
    python3 analyze_roster.py
"""

import sqlite3
from pathlib import Path
import pandas as pd

# ---------- CONFIG ----------
MY_ROSTER_ID = 5              # Huddlepuffers roster_id for Nmhochstedler
CURRENT_SEASON = "2025"
# ----------------------------

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "csv"
DB_PATH = ROOT / "db" / "fantasy.sqlite"


def tablist(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def save(df, name):
    df.to_csv(CSV / f"{name}.csv", index=False)
    print(f"  -> {name}.csv ({len(df)} rows)")


def main():
    conn = sqlite3.connect(DB_PATH)
    tables = tablist(conn)
    print(f"Tables available: {len(tables)}")

    has_fc = "fantasycalc_values" in tables
    has_weekly = "nfl_weekly_stats" in tables
    has_ids = "nfl_player_ids" in tables
    print(f"  fantasycalc_values: {has_fc}  nfl_weekly_stats: {has_weekly}  nfl_player_ids: {has_ids}")

    if not has_fc:
        print("\n!! Run fetch_fantasycalc.py first to enable valuation analysis.")
        return

    # ---- 1. Current roster with values ----
    print("\n[1/5] Your roster with dynasty values")
    my_roster = pd.read_sql("""
        SELECT rp.player_id, rp.is_starter, rp.is_taxi, rp.is_reserve,
               p.full_name, p.position, p.team, p.age, p.years_exp,
               fc.value, fc.overall_rank, fc.position_rank, fc.trend_30day,
               fc.starter_value, fc.playoff_value
        FROM roster_players rp
        LEFT JOIN players p ON p.player_id = rp.player_id
        LEFT JOIN fantasycalc_values fc ON fc.sleeper_id = rp.player_id
        WHERE rp.season = ? AND rp.roster_id = ?
        ORDER BY COALESCE(fc.value, 0) DESC
    """, conn, params=(CURRENT_SEASON, MY_ROSTER_ID))
    save(my_roster, "analysis_roster_value")

    total_value = my_roster["value"].sum()
    starter_value = my_roster[my_roster["is_starter"] == 1]["value"].sum()
    print(f"  TOTAL roster value: {total_value:,.0f}")
    print(f"  Starter value: {starter_value:,.0f}")

    # ---- 2. Every team's total dynasty value ----
    print("\n[2/5] League-wide team valuations")
    league_values = pd.read_sql("""
        SELECT r.roster_id,
               u.display_name,
               COUNT(rp.player_id) as players,
               SUM(fc.value) as total_value,
               SUM(CASE WHEN rp.is_starter THEN fc.value ELSE 0 END) as starter_value,
               AVG(p.age) as avg_age,
               r.wins, r.losses, r.fpts
        FROM rosters r
        LEFT JOIN roster_players rp ON rp.roster_id = r.roster_id AND rp.league_id = r._league_id
        LEFT JOIN players p ON p.player_id = rp.player_id
        LEFT JOIN fantasycalc_values fc ON fc.sleeper_id = rp.player_id
        LEFT JOIN users u ON u.user_id = r.owner_id AND u._league_id = r._league_id
        WHERE r._season = ?
        GROUP BY r.roster_id, u.display_name, r.wins, r.losses, r.fpts
        ORDER BY total_value DESC
    """, conn, params=(CURRENT_SEASON,))
    save(league_values, "analysis_league_valuation")

    print("\n  Rank  Team                  Value    Starter   AvgAge  Record")
    for i, row in league_values.iterrows():
        marker = "  <-- YOU" if row["roster_id"] == MY_ROSTER_ID else ""
        print(f"  {i+1:>4}  {str(row['display_name'] or '?'):<20}  {row['total_value']:>6,.0f}   {row['starter_value']:>6,.0f}   {row['avg_age']:>5.1f}   {row['wins']}-{row['losses']}{marker}")

    # ---- 3. Position strength ranking ----
    print("\n[3/5] Your position strength vs. league")
    pos_strength = pd.read_sql("""
        WITH team_pos AS (
          SELECT r.roster_id,
                 p.position,
                 SUM(fc.value) as pos_value,
                 COUNT(*) as n
          FROM rosters r
          JOIN roster_players rp ON rp.roster_id = r.roster_id AND rp.league_id = r._league_id
          JOIN players p ON p.player_id = rp.player_id
          LEFT JOIN fantasycalc_values fc ON fc.sleeper_id = rp.player_id
          WHERE r._season = ? AND p.position IN ('QB','RB','WR','TE','LB','DB','DT','DE')
          GROUP BY r.roster_id, p.position
        )
        SELECT position, roster_id, pos_value, n,
               RANK() OVER (PARTITION BY position ORDER BY pos_value DESC) as league_rank
        FROM team_pos
        ORDER BY position, league_rank
    """, conn, params=(CURRENT_SEASON,))
    my_pos = pos_strength[pos_strength["roster_id"] == MY_ROSTER_ID].copy()
    save(my_pos, "analysis_position_strength")

    print("  Pos  Rank   Value    Count")
    for _, row in my_pos.iterrows():
        print(f"  {row['position']:<4} #{int(row['league_rank']):<2}   {row['pos_value']:>6,.0f}    {row['n']}")

    # ---- 4. Age risk (sell window closing) ----
    print("\n[4/5] Age risk on your roster (players 29+ with value > 2000)")
    age_risk = my_roster[(my_roster["age"] >= 29) & (my_roster["value"] >= 2000)].copy()
    age_risk = age_risk[["full_name", "position", "team", "age", "value", "trend_30day", "overall_rank"]]
    save(age_risk, "analysis_age_risk")
    for _, row in age_risk.iterrows():
        trend = f"{row['trend_30day']:+.0f}" if pd.notna(row["trend_30day"]) else "?"
        print(f"  {row['full_name']:<22} {row['position']:<3}  age={row['age']:<4}  value={row['value']:,.0f}  30d={trend}")

    # ---- 5. Buy-low candidates (league-wide, not just your roster) ----
    print("\n[5/5] Buy-low candidates: sub-25, top-100 overall, positive 30d trend")
    buy_low = pd.read_sql("""
        SELECT full_name, position, team, age, value, overall_rank, trend_30day
        FROM fantasycalc_values
        WHERE age < 25 AND age IS NOT NULL
          AND overall_rank <= 100 AND overall_rank IS NOT NULL
          AND trend_30day > 0
        ORDER BY trend_30day DESC
        LIMIT 20
    """, conn)
    save(buy_low, "analysis_buy_low")
    for _, row in buy_low.iterrows():
        print(f"  #{int(row['overall_rank']):>3}  {row['full_name']:<22} {row['position']:<3}  age={row['age']:<4}  value={row['value']:,.0f}  30d=+{row['trend_30day']:.0f}")

    conn.close()
    print("\nAnalysis complete.")


if __name__ == "__main__":
    main()
