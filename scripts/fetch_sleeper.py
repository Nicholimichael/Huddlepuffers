"""
fetch_sleeper.py — Pull Huddlepuffers (and all leagues for a user) from the Sleeper API.

Outputs:
  - data/raw/*.json         : raw API responses (for reprocessing)
  - data/csv/*.csv          : flat, Excel-friendly tables
  - db/fantasy.sqlite       : SQLite database with indexed tables

Usage:
    python3 fetch_sleeper.py

Config is at the top of the file. No API key required.
"""

import json
import sqlite3
import sys
import time
import traceback
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

import pandas as pd

# Make project-root config importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

# ---------- CONFIG ----------
# Identity comes from config.py — single source of truth.
USERNAME = config.SLEEPER_USERNAME
LEAGUE_NAME_FILTER = config.LEAGUE_NAME_FILTER  # Set to None in config to pull ALL leagues
START_SEASON = config.CURRENT_SEASON  # walks backwards from here
MIN_SEASON = 2018
# ----------------------------

BASE = "https://api.sleeper.app/v1"
ROOT = config.PROJECT_ROOT
RAW = ROOT / "data" / "raw"
CSV = ROOT / "data" / "csv"
DB_PATH = config.DB_PATH

for d in (RAW, CSV, DB_PATH.parent):
    d.mkdir(parents=True, exist_ok=True)


def get(path, retries=3, backoff=1.5):
    url = f"{BASE}{path}"
    for i in range(retries):
        try:
            req = Request(url, headers={"User-Agent": "HossAutomation-FantasyFootball/1.0"})
            with urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except HTTPError as e:
            if e.code == 404:
                return None
            if i == retries - 1:
                raise
            time.sleep(backoff ** i)
        except URLError:
            if i == retries - 1:
                raise
            time.sleep(backoff ** i)
    return None


def save_raw(name, obj):
    (RAW / f"{name}.json").write_text(json.dumps(obj, indent=2, default=str))


def _json_safe(v):
    """Make any value safe for SQLite: dicts/lists -> JSON string, keep scalars."""
    if isinstance(v, (dict, list)):
        return json.dumps(v, default=str)
    return v


def flatten_for_db(df: pd.DataFrame) -> pd.DataFrame:
    """JSON-serialize any column that contains dicts/lists (SQLite can't store those)."""
    if df is None or df.empty:
        return df
    df = df.copy()
    for col in df.columns:
        # Check first non-null value
        sample = df[col].dropna()
        if len(sample) == 0:
            continue
        first = sample.iloc[0]
        if isinstance(first, (dict, list)):
            df[col] = df[col].apply(_json_safe)
    return df


def write_table(df, table, conn, pk=None):
    """CSV + SQLite write, defensive against nested dicts."""
    if df is None or df.empty:
        print(f"    {table}: 0 rows (skipped)")
        return
    df.to_csv(CSV / f"{table}.csv", index=False)
    safe = flatten_for_db(df)
    try:
        safe.to_sql(table, conn, if_exists="replace", index=False)
        if pk and pk in safe.columns:
            try:
                conn.execute(f'CREATE INDEX IF NOT EXISTS idx_{table}_{pk} ON "{table}"("{pk}")')
            except sqlite3.OperationalError:
                pass
        conn.commit()
        print(f"    {table}: {len(df):,} rows -> csv + db")
    except Exception as e:
        print(f"    {table}: CSV written but DB write FAILED: {e}")


def section(label):
    print(f"\n--- {label} ---")


def main():
    section("[1/8] Lookup user")
    user = get(f"/user/{USERNAME}")
    if not user or "user_id" not in user:
        sys.exit(f"Could not find Sleeper user '{USERNAME}'")
    user_id = user["user_id"]
    print(f"  user_id={user_id} display_name={user.get('display_name')}")
    save_raw("user", user)

    section(f"[2/8] Discover leagues for seasons {START_SEASON}->{MIN_SEASON}")
    all_leagues = []
    for season in range(START_SEASON, MIN_SEASON - 1, -1):
        leagues = get(f"/user/{user_id}/leagues/nfl/{season}") or []
        for lg in leagues:
            lg["_season_pulled"] = season
            all_leagues.append(lg)
        print(f"  {season}: {len(leagues)} leagues")

    if LEAGUE_NAME_FILTER:
        target = [l for l in all_leagues if LEAGUE_NAME_FILTER.lower() in (l.get("name") or "").lower()]
    else:
        target = all_leagues
    if not target:
        sys.exit(f"No leagues matched filter '{LEAGUE_NAME_FILTER}'")
    save_raw("leagues_all", all_leagues)
    save_raw("leagues_target", target)

    # Walk previous_league_id to get every season of this dynasty
    league_chain = {}
    for lg in target:
        cur = lg
        while cur and cur["league_id"] not in league_chain:
            league_chain[cur["league_id"]] = cur
            prev = cur.get("previous_league_id")
            if not prev or prev == "0":
                break
            cur = get(f"/league/{prev}")
    print(f"  full dynasty chain: {len(league_chain)} seasons")

    # Also walk forward through predecessors of targets (already in target if they're active)
    conn = sqlite3.connect(DB_PATH)

    section("[3/8] Leagues table")
    league_rows = []
    for lid, lg in league_chain.items():
        league_rows.append({
            "league_id": lid,
            "name": lg.get("name"),
            "season": lg.get("season"),
            "status": lg.get("status"),
            "sport": lg.get("sport"),
            "total_rosters": lg.get("total_rosters"),
            "previous_league_id": lg.get("previous_league_id"),
            "draft_id": lg.get("draft_id"),
            "settings_json": json.dumps(lg.get("settings") or {}),
            "scoring_json": json.dumps(lg.get("scoring_settings") or {}),
            "roster_positions_json": json.dumps(lg.get("roster_positions") or []),
        })
    write_table(pd.DataFrame(league_rows), "leagues", conn, pk="league_id")

    # Aggregators
    all_users, all_rosters, all_matchups, all_tx = [], [], [], []
    all_drafts, all_picks, all_traded_picks = [], [], []

    section(f"[4/8] Per-season pulls ({len(league_chain)} seasons)")
    for lid, lg in league_chain.items():
        season = lg.get("season")
        print(f"\n  Season {season} ({lid})")
        try:
            users = get(f"/league/{lid}/users") or []
            for u in users:
                u["_league_id"] = lid; u["_season"] = season
            all_users.extend(users)
            print(f"    users: {len(users)}")

            rosters = get(f"/league/{lid}/rosters") or []
            for r in rosters:
                r["_league_id"] = lid; r["_season"] = season
            all_rosters.extend(rosters)
            print(f"    rosters: {len(rosters)}")

            settings = lg.get("settings") or {}
            playoff_start = settings.get("playoff_week_start") or 15
            last_week = max(playoff_start + 3, 18)
            season_matchups = 0
            season_tx = 0
            for wk in range(1, last_week + 1):
                m = get(f"/league/{lid}/matchups/{wk}") or []
                for x in m:
                    x["_league_id"] = lid; x["_season"] = season; x["_week"] = wk
                all_matchups.extend(m); season_matchups += len(m)

                tx = get(f"/league/{lid}/transactions/{wk}") or []
                for x in tx:
                    x["_league_id"] = lid; x["_season"] = season; x["_week"] = wk
                all_tx.extend(tx); season_tx += len(tx)
            print(f"    matchups: {season_matchups}, transactions: {season_tx}")

            drafts = get(f"/league/{lid}/drafts") or []
            for d in drafts:
                d["_league_id"] = lid; d["_season"] = season
                all_drafts.append(d)
                picks = get(f"/draft/{d['draft_id']}/picks") or []
                for p in picks:
                    p["_league_id"] = lid; p["_season"] = season; p["_draft_id"] = d["draft_id"]
                all_picks.extend(picks)
            print(f"    drafts: {len(drafts)}")

            tp = get(f"/league/{lid}/traded_picks") or []
            for p in tp:
                p["_league_id"] = lid; p["_season"] = season
            all_traded_picks.extend(tp)
            print(f"    traded_picks: {len(tp)}")
        except Exception as e:
            print(f"    !! season {season} partial failure: {e}")
            traceback.print_exc()

    section("[5/8] Flatten & write tables")

    # Users
    try:
        write_table(pd.json_normalize(all_users), "users", conn, pk="user_id")
    except Exception as e:
        print(f"    users write failed: {e}")

    # Rosters — build flat row + side table for player assignments
    try:
        roster_rows, roster_player_rows = [], []
        NESTED_FIELDS = {"players", "starters", "reserve", "taxi", "metadata", "settings", "co_owners", "keepers", "player_map"}
        for r in all_rosters:
            rr = {k: v for k, v in r.items() if k not in NESTED_FIELDS}
            rr["metadata_json"] = json.dumps(r.get("metadata") or {}, default=str)
            rr["starters_json"] = json.dumps(r.get("starters") or [])
            rr["reserve_json"] = json.dumps(r.get("reserve") or [])
            rr["taxi_json"] = json.dumps(r.get("taxi") or [])
            rr["settings_json"] = json.dumps(r.get("settings") or {}, default=str)
            rr["co_owners_json"] = json.dumps(r.get("co_owners") or [])
            rr["player_map_json"] = json.dumps(r.get("player_map") or {}, default=str)
            # Extract common settings fields to their own columns for easy querying
            s = r.get("settings") or {}
            rr["wins"] = s.get("wins")
            rr["losses"] = s.get("losses")
            rr["ties"] = s.get("ties")
            rr["fpts"] = (s.get("fpts") or 0) + (s.get("fpts_decimal") or 0) / 100.0 if s.get("fpts") is not None else None
            rr["fpts_against"] = (s.get("fpts_against") or 0) + (s.get("fpts_against_decimal") or 0) / 100.0 if s.get("fpts_against") is not None else None
            rr["ppts"] = (s.get("ppts") or 0) + (s.get("ppts_decimal") or 0) / 100.0 if s.get("ppts") is not None else None
            rr["waiver_budget_used"] = s.get("waiver_budget_used")
            rr["waiver_position"] = s.get("waiver_position")
            rr["total_moves"] = s.get("total_moves")
            roster_rows.append(rr)

            players = r.get("players") or []
            starters = set(r.get("starters") or [])
            taxi = set(r.get("taxi") or [])
            reserve = set(r.get("reserve") or [])
            for pid in players:
                if pid is None:
                    continue
                roster_player_rows.append({
                    "league_id": r["_league_id"],
                    "season": r["_season"],
                    "roster_id": r.get("roster_id"),
                    "owner_id": r.get("owner_id"),
                    "player_id": pid,
                    "is_starter": pid in starters,
                    "is_taxi": pid in taxi,
                    "is_reserve": pid in reserve,
                })
        write_table(pd.DataFrame(roster_rows), "rosters", conn, pk="roster_id")
        write_table(pd.DataFrame(roster_player_rows), "roster_players", conn, pk="player_id")
    except Exception as e:
        print(f"    rosters write failed: {e}")
        traceback.print_exc()

    # Matchups
    try:
        write_table(pd.json_normalize(all_matchups, sep="_"), "matchups", conn, pk="roster_id")
    except Exception as e:
        print(f"    matchups write failed: {e}")

    # Transactions
    try:
        write_table(pd.json_normalize(all_tx, sep="_"), "transactions", conn, pk="transaction_id")
    except Exception as e:
        print(f"    transactions write failed: {e}")

    # Drafts + picks
    try:
        write_table(pd.json_normalize(all_drafts, sep="_"), "drafts", conn, pk="draft_id")
    except Exception as e:
        print(f"    drafts write failed: {e}")
    try:
        write_table(pd.json_normalize(all_picks, sep="_"), "draft_picks", conn, pk="draft_id")
    except Exception as e:
        print(f"    draft_picks write failed: {e}")

    # Traded picks
    try:
        write_table(pd.json_normalize(all_traded_picks, sep="_"), "traded_picks", conn, pk="league_id")
    except Exception as e:
        print(f"    traded_picks write failed: {e}")

    section("[6/8] NFL player database (~5MB, one-time refresh)")
    try:
        players = get("/players/nfl") or {}
        save_raw("players_nfl", players)
        player_rows = []
        for pid, p in players.items():
            player_rows.append({
                "player_id": pid,
                "full_name": p.get("full_name"),
                "first_name": p.get("first_name"),
                "last_name": p.get("last_name"),
                "position": p.get("position"),
                "team": p.get("team"),
                "age": p.get("age"),
                "years_exp": p.get("years_exp"),
                "status": p.get("status"),
                "college": p.get("college"),
                "birth_date": p.get("birth_date"),
                "height": p.get("height"),
                "weight": p.get("weight"),
                "fantasy_positions": ",".join(p.get("fantasy_positions") or []),
                "depth_chart_position": p.get("depth_chart_position"),
                "depth_chart_order": p.get("depth_chart_order"),
                "injury_status": p.get("injury_status"),
                "number": p.get("number"),
                "search_rank": p.get("search_rank"),
            })
        write_table(pd.DataFrame(player_rows), "players", conn, pk="player_id")
    except Exception as e:
        print(f"    players write failed: {e}")
        traceback.print_exc()

    section("[7/8] NFL state (current week/season)")
    try:
        state = get("/state/nfl")
        if state:
            save_raw("state_nfl", state)
            write_table(pd.DataFrame([state]), "nfl_state", conn)
    except Exception as e:
        print(f"    nfl_state write failed: {e}")

    section("[8/8] Summary")
    cur = conn.cursor()
    for t in sorted(r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")):
        n = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        print(f"  {t}: {n:,} rows")
    conn.close()
    print(f"\nDone. DB: {DB_PATH}")


if __name__ == "__main__":
    main()
