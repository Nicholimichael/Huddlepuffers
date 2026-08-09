"""
build_extras_v3.py — augments rankings_data.json with three new modules:

  1. extras.rookies         : top rookies (years_exp == 0) joined with FC dynasty value
  2. extras.team_context    : per-NFL-team 2024 offensive aggregates + 1-32 ranks
  3. extras.snap_opportunity: per-Huddlepuffers-rostered player, last 8 games of
                              snap% / target-share / carry-share with linear slope

Idempotent — safe to re-run after build_platform_v2.py.
"""

import os
import sys
import json
import math
import sqlite3
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Make project-root config importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

HERE = config.PLATFORM_DIR
PROJECT = config.PROJECT_ROOT
DB = config.DB_PATH
RANKINGS_JSON = HERE / "rankings_data.json"

# Where to take snap data from. config.SNAP_DATA_SEASON is the *ceiling*; during
# the offseason the current season has no snaps yet, so cap at what the DB
# actually holds (otherwise every snap query hits an empty season and the whole
# view silently renders blank — happened at the 2026 rollover).
RECENT_GAMES = 8


def _max_db_season(table, ceiling):
    """Most recent season present in `table`, capped at `ceiling`; ceiling if unknown."""
    try:
        import sqlite3 as _sq
        con = _sq.connect(str(DB))
        row = con.execute(f'SELECT MAX(season) FROM "{table}" WHERE season <= ?',
                          (ceiling,)).fetchone()
        con.close()
        if row and row[0] is not None:
            return int(row[0])
    except Exception:
        pass
    return ceiling


TARGET_SNAP_SEASON = _max_db_season("nfl_snap_counts", config.SNAP_DATA_SEASON)
if TARGET_SNAP_SEASON != config.SNAP_DATA_SEASON:
    print(f"[extras_v3] snap season capped to {TARGET_SNAP_SEASON} "
          f"(config ceiling {config.SNAP_DATA_SEASON} has no data yet)")

# Where to take team-context aggregates from (need full weekly_stats coverage).
TARGET_TEAM_SEASON = _max_db_season("nfl_weekly_stats", config.LAST_COMPLETE_SEASON)
if TARGET_TEAM_SEASON != config.LAST_COMPLETE_SEASON:
    print(f"::warning::[extras_v3] team context anchored to {TARGET_TEAM_SEASON} — "
          f"weekly stats for {config.LAST_COMPLETE_SEASON} not in DB")


from lib.utils import clean_num


def linear_slope(xs, ys):
    """Simple least-squares slope of ys over xs. Returns 0 for n<2."""
    n = len(xs)
    if n < 2:
        return 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den = sum((x - mean_x) ** 2 for x in xs)
    return num / den if den else 0.0


def build_hall_of_fame():
    """League history: banners, toilet bowls, and the all-time record book.

    Reads leagues/rosters/users/matchups/brackets from SQLite. Defensive
    throughout — a season with no bracket data simply gets no banner, and a
    missing brackets table (stale DB) degrades to {"available": False}.
    """
    con = sqlite3.connect(str(DB))

    def q(sql, params=()):
        try:
            cur = con.execute(sql, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
        except sqlite3.OperationalError as e:
            print(f"      hall_of_fame query skipped: {e}")
            return []

    leagues = q("SELECT league_id, name, season, settings_json, total_rosters FROM leagues")
    if not leagues:
        con.close()
        return {"available": False}
    for lg in leagues:
        try:
            lg["settings"] = json.loads(lg.get("settings_json") or "{}")
        except Exception:
            lg["settings"] = {}
        lg["season"] = int(lg["season"])
    leagues.sort(key=lambda x: x["season"])

    rosters = q("""SELECT _league_id, _season, roster_id, owner_id,
                          wins, losses, ties, fpts, fpts_against FROM rosters""")
    users = q("SELECT * FROM users")
    matchups = q("""SELECT _league_id, _season, _week AS week, roster_id,
                           matchup_id, points FROM matchups""")
    brackets = q("""SELECT _league_id, _season, _bracket, r, t1, t2, w, l, p
                    FROM brackets""")
    con.close()

    # owner display name per (league_id, user_id); team_name column name varies
    # with json_normalize ("metadata.team_name").
    tn_key = next((k for k in (users[0].keys() if users else [])
                   if k.endswith("team_name")), None)
    uname = {}
    for u in users:
        uname[(u.get("_league_id"), str(u.get("user_id")))] = {
            "display_name": u.get("display_name") or "?",
            "team_name": (u.get(tn_key) if tn_key else None) or None,
        }

    # per-league roster lookup
    ros_by_league = defaultdict(dict)
    for r in rosters:
        ros_by_league[r["_league_id"]][int(r["roster_id"])] = r

    def entry(lid, roster_id):
        """Season-scoped identity + regular-season line for one roster."""
        if roster_id is None:
            return None
        r = ros_by_league.get(lid, {}).get(int(roster_id))
        if not r:
            return None
        u = uname.get((lid, str(r.get("owner_id"))), {})
        return {
            "roster_id":  int(roster_id),
            "owner_id":   r.get("owner_id"),
            "owner_name": u.get("display_name") or "?",
            "team_name":  u.get("team_name"),
            "wins":   int(r.get("wins") or 0),
            "losses": int(r.get("losses") or 0),
            "ties":   int(r.get("ties") or 0),
            "fpts":   round(float(r.get("fpts") or 0), 1),
        }

    # matchup pairs per (league, week): [{roster_id, points}, ...] by matchup_id
    games = defaultdict(list)   # (lid, week, matchup_id) -> rows
    for m in matchups:
        if m.get("matchup_id") is None:
            continue
        games[(m["_league_id"], int(m["week"]), int(m["matchup_id"]))].append(m)

    def playoff_week_start(lg):
        try:
            return int(lg["settings"].get("playoff_week_start") or 15)
        except Exception:
            return 15

    lg_by_id = {lg["league_id"]: lg for lg in leagues}

    # ---- season summaries (banners) ----
    seasons_out = []
    titles = defaultdict(int); runner_ups = defaultdict(int)
    toilets = defaultdict(int); playoff_apps = defaultdict(set)
    for lg in leagues:
        lid = lg["league_id"]; season = lg["season"]
        wb = [b for b in brackets if b["_league_id"] == lid and b["_bracket"] == "winners"]
        lb = [b for b in brackets if b["_league_id"] == lid and b["_bracket"] == "losers"]
        final = next((b for b in wb if b.get("p") == 1 and b.get("w") is not None), None)
        if not final:
            continue  # season not finished (or bracket missing) — no banner
        third_g = next((b for b in wb if b.get("p") == 3 and b.get("w") is not None), None)

        def _rid(x):
            """Bracket roster refs come out of SQLite as floats (1.0) — normalize."""
            try:
                return int(float(x))
            except (TypeError, ValueError):
                return None

        # playoff field = everyone who appears in the winners bracket
        wb_teams = {_rid(x) for b in wb
                    for x in (b.get("t1"), b.get("t2"), b.get("w"), b.get("l"))} - {None}
        for rid in wb_teams:
            playoff_apps[rid].add(season)

        # non-playoff field: losers-bracket participants; fallback = standings bottom
        lb_teams = {_rid(x) for b in lb for x in (b.get("t1"), b.get("t2"))} - {None}
        if not lb_teams:
            n_playoff = int(lg["settings"].get("playoff_teams") or 6)
            standings = sorted(ros_by_league.get(lid, {}).values(),
                               key=lambda r: (int(r.get("wins") or 0),
                                              float(r.get("fpts") or 0)))
            lb_teams = {int(r["roster_id"])
                        for r in standings[:max(0, (lg.get("total_rosters") or 10) - n_playoff)]}

        # league rule: rank the bottom group by regular-season points, fewest first
        bottom = [entry(lid, rid) for rid in lb_teams]
        bottom = sorted([b for b in bottom if b], key=lambda e: e["fpts"])
        for i, b in enumerate(bottom):
            b["pick"] = f"1.{i + 1:02d}"
        toilet = bottom[0] if bottom else None
        if toilet:
            toilets[toilet["roster_id"]] += 1

        champ = entry(lid, final.get("w"))
        runner = entry(lid, final.get("l"))
        if champ:
            titles[champ["roster_id"]] += 1
        if runner:
            runner_ups[runner["roster_id"]] += 1

        best_rec = None
        rows = list(ros_by_league.get(lid, {}).values())
        if rows:
            top = max(rows, key=lambda r: (int(r.get("wins") or 0), float(r.get("fpts") or 0)))
            best_rec = entry(lid, top["roster_id"])

        seasons_out.append({
            "season":      season,
            "league_name": lg.get("name"),
            "champion":    champ,
            "runner_up":   runner,
            "third":       entry(lid, third_g.get("w")) if third_g else None,
            "toilet":      toilet,
            "bottom4":     bottom,
            "best_record": best_rec,
        })
    seasons_out.sort(key=lambda s: -s["season"])

    # ---- game-level record book ----
    played = []  # {season, week, lid, roster_id, points, opp_id, opp_points, playoff}
    for (lid, week, _mid), rows in games.items():
        if len(rows) != 2:
            continue
        p1, p2 = rows
        pts1 = float(p1.get("points") or 0); pts2 = float(p2.get("points") or 0)
        if pts1 + pts2 <= 0:
            continue  # unplayed / future week
        lg = lg_by_id.get(lid)
        if not lg:
            continue
        po = week >= playoff_week_start(lg)
        season = lg["season"]
        played.append({"lid": lid, "season": season, "week": week, "playoff": po,
                       "roster_id": int(p1["roster_id"]), "points": pts1,
                       "opp_id": int(p2["roster_id"]), "opp_points": pts2})
        played.append({"lid": lid, "season": season, "week": week, "playoff": po,
                       "roster_id": int(p2["roster_id"]), "points": pts2,
                       "opp_id": int(p1["roster_id"]), "opp_points": pts1})

    def _fmt(v):
        """2-dp string, trailing zeros stripped. Strings survive the payload
        diet in build_redesign.py, which rounds every FLOAT to 1 decimal —
        that would turn a 0.02-point closest game into '+0'."""
        return ("%.2f" % v).rstrip("0").rstrip(".")

    def gref(g):
        e = entry(g["lid"], g["roster_id"]) or {}
        o = entry(g["lid"], g["opp_id"]) or {}
        return {"owner_name": e.get("owner_name", "?"), "roster_id": g["roster_id"],
                "season": g["season"], "week": g["week"], "playoff": g["playoff"],
                "points": _fmt(g["points"]), "opp_name": o.get("owner_name", "?"),
                "opp_points": _fmt(g["opp_points"]),
                "margin": _fmt(g["points"] - g["opp_points"])}

    records = {}
    if played:
        records["high_week"] = gref(max(played, key=lambda g: g["points"]))
        records["low_week"] = gref(min(played, key=lambda g: g["points"]))
        wins_only = [g for g in played if g["points"] > g["opp_points"]]
        losses_only = [g for g in played if g["points"] < g["opp_points"]]
        if wins_only:
            records["blowout"] = gref(max(wins_only, key=lambda g: g["points"] - g["opp_points"]))
            records["closest"] = gref(min(wins_only, key=lambda g: g["points"] - g["opp_points"]))
            records["fewest_pts_win"] = gref(min(wins_only, key=lambda g: g["points"]))
        if losses_only:
            records["most_pts_loss"] = gref(max(losses_only, key=lambda g: g["points"]))
    top_weeks = [gref(g) for g in sorted(played, key=lambda g: -g["points"])[:10]]

    # season-total records (regular season, finished seasons only)
    fin_lids = {s["season"]: True for s in seasons_out}
    season_totals = []
    for lg in leagues:
        if not fin_lids.get(lg["season"]):
            continue
        for r in ros_by_league.get(lg["league_id"], {}).values():
            e = entry(lg["league_id"], r["roster_id"])
            if e and e["fpts"] > 0:
                season_totals.append({**e, "season": lg["season"]})
    if season_totals:
        records["high_season"] = max(season_totals, key=lambda e: e["fpts"])
        records["low_season"] = min(season_totals, key=lambda e: e["fpts"])

    # ---- streaks (regular season, may span seasons; franchise = roster_id) ----
    reg = sorted((g for g in played if not g["playoff"]),
                 key=lambda g: (g["season"], g["week"]))
    by_franchise = defaultdict(list)
    for g in reg:
        res = "W" if g["points"] > g["opp_points"] else ("L" if g["points"] < g["opp_points"] else "T")
        by_franchise[g["roster_id"]].append({**g, "res": res})
    best_w = best_l = None
    for rid, gs in by_franchise.items():
        run = 0; kind = None; start = None
        for g in gs + [{"res": "END"}]:
            if g["res"] == kind and kind in ("W", "L"):
                run += 1
            else:
                if kind in ("W", "L") and run >= 2:
                    rec = {"roster_id": rid, "length": run, "kind": kind,
                           "from": {"season": start["season"], "week": start["week"]},
                           "to": {"season": prev["season"], "week": prev["week"]},
                           "owner_name": (entry(prev["lid"], rid) or {}).get("owner_name", "?")}
                    if kind == "W" and (not best_w or run > best_w["length"]):
                        best_w = rec
                    if kind == "L" and (not best_l or run > best_l["length"]):
                        best_l = rec
                kind = g["res"] if g["res"] in ("W", "L") else None
                run = 1; start = g if kind else None
            prev = g
    if best_w:
        records["win_streak"] = best_w
    if best_l:
        records["loss_streak"] = best_l

    # ---- franchise all-time table (franchise = roster_id, name = latest owner) ----
    latest_owner = {}
    for lg in leagues:  # ascending season order → last write wins
        for rid in ros_by_league.get(lg["league_id"], {}):
            e = entry(lg["league_id"], rid)
            if e:
                latest_owner[rid] = e
    franchises = []
    for rid, cur_e in latest_owner.items():
        W = L = T = 0; pf = pa = 0.0; n_seasons = 0
        for lg in leagues:
            r = ros_by_league.get(lg["league_id"], {}).get(rid)
            if not r:
                continue
            gp = int(r.get("wins") or 0) + int(r.get("losses") or 0) + int(r.get("ties") or 0)
            if gp == 0:
                continue
            n_seasons += 1
            W += int(r.get("wins") or 0); L += int(r.get("losses") or 0)
            T += int(r.get("ties") or 0)
            pf += float(r.get("fpts") or 0); pa += float(r.get("fpts_against") or 0)
        franchises.append({
            "roster_id": rid, "owner_name": cur_e["owner_name"],
            "team_name": cur_e.get("team_name"), "seasons": n_seasons,
            "wins": W, "losses": L, "ties": T,
            "win_pct": round(100.0 * W / max(W + L + T, 1), 1),
            "pf": round(pf, 1), "pa": round(pa, 1),
            "titles": titles.get(rid, 0), "runner_ups": runner_ups.get(rid, 0),
            "toilets": toilets.get(rid, 0),
            "playoff_apps": len(playoff_apps.get(rid, ())),
        })
    franchises.sort(key=lambda f: (-f["titles"], -f["win_pct"]))

    return {
        "available": bool(seasons_out),
        "seasons": seasons_out,
        "franchises": franchises,
        "records": records,
        "top_weeks": top_weeks,
        "rule_note": "Toilet bowl / 1.01 order: fewest regular-season points among the non-playoff teams.",
    }


def main():
    print(f"[extras_v3] Loading {RANKINGS_JSON}")
    with open(RANKINGS_JSON) as f:
        data = json.load(f)

    players = data["players"]
    picks = data["picks"]
    extras = data.setdefault("extras", {})

    # ──────────────────────────────────────────────────────────
    # 1) Rookies
    # years_exp == 0 → incoming 2026 NFL draft class (all FA pre-draft).
    # years_exp == 1 → most recent dynasty draftees (rostered).
    # We expose both pools and let the UI pivot.
    # ──────────────────────────────────────────────────────────
    print("[extras_v3] Building rookies module")
    incoming = []        # years_exp == 0
    second_year = []     # years_exp == 1 — last year's rookie class
    for p in players:
        yrs = p.get("years_exp")
        if yrs is None:
            continue
        record = {
            "player_id":   p.get("player_id"),
            "full_name":   p.get("full_name"),
            "position":    p.get("position"),
            "team":        p.get("team"),
            "age":         clean_num(p.get("age")),
            "owner_id":    p.get("owner_id"),
            "owner_name":  p.get("owner_name") or "FA",
            "rostered":    bool(p.get("rostered")),
            "fc_dyn":      clean_num(p.get("fc_dyn")),
            "fc_dyn_rank": clean_num(p.get("fc_dyn_rank")),
            "trend_30d":   clean_num(p.get("trend_30day")),
            "dynasty_score":   clean_num(p.get("dynasty_score")),
            "dynasty_overall_rank": clean_num(p.get("dynasty_overall_rank")),
            "is_taxi":     bool(p.get("is_taxi")),
            "yrs_exp":     int(yrs),
        }
        if yrs == 0:
            incoming.append(record)
        elif yrs == 1:
            second_year.append(record)

    incoming.sort(key=lambda r: (r["fc_dyn"] is None, -(r["fc_dyn"] or 0)))
    second_year.sort(key=lambda r: (r["fc_dyn"] is None, -(r["fc_dyn"] or 0)))
    # Combined "rookies" list for backwards compatibility
    rookie_players = incoming + second_year

    # Add upcoming-draft-class rookie picks from the picks list
    next_draft_prefix = f"{config.NEXT_DRAFT_SEASON} "
    pick_2026 = []  # variable name kept for downstream compatibility (= next-draft picks)
    for pk in picks:
        nm = pk.get("full_name") or ""
        if not nm.startswith(next_draft_prefix):
            continue
        pick_2026.append({
            "label":     nm,
            "fc_dyn":    clean_num(pk.get("trade_dyn_value")),
            "overall_rank": clean_num(pk.get("overall_rank")),
        })
    pick_2026.sort(key=lambda r: (r["fc_dyn"] is None, -(r["fc_dyn"] or 0)))

    # Owner-by-owner rookie capital. We count BOTH:
    #   - dynasty value of rostered 2nd-year players (last year's rooks)
    #   - dynasty value of 2026 rookie picks owned (from extras.future_picks)
    by_owner = defaultdict(lambda: {
        "players": 0, "young_value": 0,
        "picks": 0, "pick_value": 0,
    })
    for r in second_year:
        if r["owner_name"] == "FA" or not r["fc_dyn"]:
            continue
        by_owner[r["owner_name"]]["players"] += 1
        by_owner[r["owner_name"]]["young_value"] += r["fc_dyn"]

    # Layer in 2026 rookie picks each owner holds (from existing future_picks)
    fp = extras.get("future_picks", {})
    pick_matrix = fp.get("matrix", []) if isinstance(fp, dict) else []
    for team_picks in pick_matrix:
        owner = team_picks.get("owner_name")
        if not owner:
            continue
        for pk in team_picks.get("picks", []):
            if pk.get("season") != config.NEXT_DRAFT_SEASON:
                continue
            by_owner[owner]["picks"] += 1
            by_owner[owner]["pick_value"] += pk.get("value", 0) or 0

    rookie_capital = []
    for owner, stats in by_owner.items():
        rookie_capital.append({
            "owner_name":  owner,
            "young_players": stats["players"],
            "young_value":   round(stats["young_value"]),
            "picks_2026":    stats["picks"],  # field name kept for backwards compat
            "pick_value":    round(stats["pick_value"]),
            "total_value":   round(stats["young_value"] + stats["pick_value"]),
        })
    rookie_capital.sort(key=lambda r: -r["total_value"])

    extras["rookies"] = {
        "incoming_class":  incoming,
        "second_year":     second_year,
        "rookies":         rookie_players,  # combined list
        "top_picks":       pick_2026,
        "owner_capital":   rookie_capital,
        "season":          config.NEXT_DRAFT_SEASON,
    }
    print(f"      incoming(yrs=0): {len(incoming)}  "
          f"2nd-yr(yrs=1): {len(second_year)}  picks: {len(pick_2026)}  "
          f"owners w/ capital: {len(rookie_capital)}")

    # ──────────────────────────────────────────────────────────
    # 2) NFL Team Context
    # ──────────────────────────────────────────────────────────
    print(f"[extras_v3] Building NFL team context (season={TARGET_TEAM_SEASON})")
    if not DB.exists():
        print(f"      DB missing at {DB}; skipping team_context")
        extras["team_context"] = {"available": False}
    else:
        con = sqlite3.connect(str(DB))
        # We aggregate at the team level. Note: defensive stats (sacks
        # taken) are *against* the team, so not strictly offensive — fine
        # for context purposes.
        sql = f"""
        SELECT
            recent_team AS team,
            COUNT(DISTINCT week)              AS games,
            SUM(COALESCE(attempts, 0))         AS pass_attempts,
            SUM(COALESCE(completions, 0))      AS completions,
            SUM(COALESCE(passing_yards, 0))    AS passing_yards,
            SUM(COALESCE(passing_tds, 0))      AS passing_tds,
            SUM(COALESCE(carries, 0))          AS carries,
            SUM(COALESCE(rushing_yards, 0))    AS rushing_yards,
            SUM(COALESCE(rushing_tds, 0))      AS rushing_tds,
            SUM(COALESCE(targets, 0))          AS targets,
            SUM(COALESCE(receptions, 0))       AS receptions,
            SUM(COALESCE(receiving_yards, 0))  AS receiving_yards,
            SUM(COALESCE(receiving_tds, 0))    AS receiving_tds,
            SUM(COALESCE(fantasy_points_ppr, 0)) AS fpts_ppr_total
        FROM nfl_weekly_stats
        WHERE season = {TARGET_TEAM_SEASON}
          AND season_type = 'REG'
          AND recent_team IS NOT NULL
          AND recent_team <> ''
        GROUP BY recent_team
        """
        cur = con.execute(sql)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        team_rows = [dict(zip(cols, r)) for r in rows]

        # Per-game derived metrics
        for t in team_rows:
            g = max(t["games"], 1)
            # Note: receptions ~ pass completions, but in team-totals we
            # double-count receivers vs. QB. Use QB attempts/completions
            # for pass volume, RB carries for rush volume.
            t["plays_per_game"]    = round((t["pass_attempts"] + t["carries"]) / g, 1)
            t["pass_per_game"]     = round(t["pass_attempts"] / g, 1)
            t["rush_per_game"]     = round(t["carries"] / g, 1)
            t["pass_yards_pg"]     = round(t["passing_yards"] / g, 1)
            t["rush_yards_pg"]     = round(t["rushing_yards"] / g, 1)
            t["total_tds_pg"]      = round((t["passing_tds"] + t["rushing_tds"]) / g, 2)
            t["pass_pct"]          = round(
                100.0 * t["pass_attempts"] / max(t["pass_attempts"] + t["carries"], 1), 1)
            t["fpts_ppr_pg"]       = round(t["fpts_ppr_total"] / g, 1)

        # Rank 1..N on each metric (1 = best for "more is more" stats)
        rank_metrics = [
            "plays_per_game", "pass_per_game", "rush_per_game",
            "pass_yards_pg",  "rush_yards_pg", "total_tds_pg",
            "fpts_ppr_pg",
        ]
        ranks = {}
        for m in rank_metrics:
            ordered = sorted(team_rows, key=lambda x: -x[m])
            for i, t in enumerate(ordered, start=1):
                ranks.setdefault(t["team"], {})[m + "_rank"] = i

        # Pace tier label for the on-card chip
        for t in team_rows:
            r = ranks.get(t["team"], {})
            t.update(r)
            # one-line tag
            tags = []
            if r.get("pass_per_game_rank", 33) <= 8:
                tags.append("high pass volume")
            elif r.get("pass_per_game_rank", 33) >= 25:
                tags.append("low pass volume")
            if r.get("rush_per_game_rank", 33) <= 8:
                tags.append("run-heavy")
            elif r.get("rush_per_game_rank", 33) >= 25:
                tags.append("pass-leaning")
            if r.get("total_tds_pg_rank", 33) <= 5:
                tags.append("top-5 scoring")
            elif r.get("total_tds_pg_rank", 33) >= 27:
                tags.append("low scoring")
            t["context_tag"] = " · ".join(tags) if tags else "average offense"

        extras["team_context"] = {
            "available": True,
            "season":    TARGET_TEAM_SEASON,
            "teams":     sorted(team_rows, key=lambda x: x["team"]),
        }
        print(f"      {len(team_rows)} teams · ranking on {len(rank_metrics)} metrics")

    # ──────────────────────────────────────────────────────────
    # 3) Snap Share & Opportunity
    # ──────────────────────────────────────────────────────────
    print(f"[extras_v3] Building snap opportunity (season={TARGET_SNAP_SEASON}, last {RECENT_GAMES})")
    if not DB.exists():
        extras["snap_opportunity"] = {"available": False}
    else:
        con = sqlite3.connect(str(DB))

        # Build sleeper_id -> pfr_id lookup. NOTE: sleeper_id in
        # nfl_player_ids comes back as a float (e.g. 12522.0) so we
        # normalize to "12522" before keying.
        def _norm_sid(v):
            if v is None or v == "":
                return None
            try:
                return str(int(float(v)))
            except (TypeError, ValueError):
                return str(v)

        crosswalk = {}
        for row in con.execute("""
            SELECT sleeper_id, pfr_id
            FROM nfl_player_ids
            WHERE sleeper_id IS NOT NULL AND sleeper_id <> ''
              AND pfr_id IS NOT NULL AND pfr_id <> ''
        """):
            sid = _norm_sid(row[0])
            if sid:
                crosswalk[sid] = row[1]

        # Get snap counts for the target season, ordered by week
        snap_rows = con.execute(f"""
            SELECT pfr_player_id, week, opponent, offense_snaps, offense_pct,
                   team, position
            FROM nfl_snap_counts
            WHERE season = {TARGET_SNAP_SEASON}
              AND game_type IN ('REG','POST')
            ORDER BY pfr_player_id, week
        """).fetchall()

        snaps_by_pfr = defaultdict(list)
        for pfr_id, wk, opp, snaps, pct, team, pos in snap_rows:
            if pfr_id is None:
                continue
            snaps_by_pfr[pfr_id].append({
                "week": int(wk),
                "opp":  opp,
                "team": team,
                "snaps": int(snaps or 0),
                "snap_pct": round(float(pct or 0) * 100, 1) if (pct or 0) <= 1 else round(float(pct or 0), 1),
                "position": pos,
            })

        # Pull rostered players' weekly target/carry counts from weekly_stats
        # (note: weekly_stats only goes through 2024, so target/carry trend uses 2024)
        wk_rows = con.execute("""
            SELECT player_id, week, opponent_team,
                   COALESCE(targets, 0) AS targets,
                   COALESCE(carries, 0) AS carries,
                   COALESCE(receptions, 0) AS receptions,
                   COALESCE(fantasy_points_ppr, 0) AS ppr
            FROM nfl_weekly_stats
            WHERE season = (SELECT MAX(season) FROM nfl_weekly_stats)
              AND season_type = 'REG'
            ORDER BY player_id, week
        """).fetchall()
        wk_by_sleeper = defaultdict(list)
        for sid, wk, opp, tgts, car, rec, ppr in wk_rows:
            if sid is None:
                continue
            wk_by_sleeper[str(sid)].append({
                "week": int(wk), "opp": opp,
                "targets": int(tgts), "carries": int(car),
                "receptions": int(rec), "ppr": float(ppr),
            })

        latest_weekly_season = con.execute(
            "SELECT MAX(season) FROM nfl_weekly_stats").fetchone()[0]

        con.close()

        # Build per-player series for rostered offensive players
        snap_records = []
        for p in players:
            if not p.get("rostered"):
                continue
            if p.get("position") not in ("QB", "RB", "WR", "TE"):
                continue
            sid = _norm_sid(p.get("player_id"))
            pfr = crosswalk.get(sid) if sid else None

            snap_series = []
            if pfr and pfr in snaps_by_pfr:
                snap_series = snaps_by_pfr[pfr][-RECENT_GAMES:]

            stat_series = []
            if sid in wk_by_sleeper:
                stat_series = wk_by_sleeper[sid][-RECENT_GAMES:]

            if not snap_series and not stat_series:
                continue

            # Slope on snap_pct (signal: trending up/down)
            snap_xs = list(range(1, len(snap_series) + 1))
            snap_ys = [s["snap_pct"] for s in snap_series]
            snap_slope = linear_slope(snap_xs, snap_ys) if snap_ys else 0.0
            snap_avg = round(sum(snap_ys) / len(snap_ys), 1) if snap_ys else None

            # Last 4 average vs prior 4 (for delta visualization)
            snap_recent4 = snap_ys[-4:]
            snap_prior4  = snap_ys[-8:-4] if len(snap_ys) >= 5 else []
            snap_delta_4v4 = round(
                (sum(snap_recent4) / len(snap_recent4)) -
                (sum(snap_prior4)  / len(snap_prior4))
                , 1
            ) if snap_recent4 and snap_prior4 else None

            # Targets & carries trend (from weekly_stats, may be 2024)
            tgt_series = [s["targets"] for s in stat_series]
            car_series = [s["carries"] for s in stat_series]
            tgt_avg = round(sum(tgt_series) / len(tgt_series), 1) if tgt_series else None
            car_avg = round(sum(car_series) / len(car_series), 1) if car_series else None

            snap_records.append({
                "player_id":  sid,
                "full_name":  p.get("full_name"),
                "position":   p.get("position"),
                "team":       p.get("team"),
                "owner_name": p.get("owner_name"),
                "rostered":   True,
                "snap_avg_pct":   snap_avg,
                "snap_slope":     round(snap_slope, 2),
                "snap_delta_4v4": snap_delta_4v4,
                "tgt_avg":        tgt_avg,
                "car_avg":        car_avg,
                "snap_series":    snap_series,
                "stat_series":    stat_series,
            })

        # Sort by combined opportunity signal: high snap_pct then rising slope
        snap_records.sort(
            key=lambda r: -((r["snap_avg_pct"] or 0) + (r["snap_slope"] or 0) * 2)
        )

        extras["snap_opportunity"] = {
            "available":             True,
            "snap_season":           TARGET_SNAP_SEASON,
            "stat_season":           latest_weekly_season,
            "recent_games":          RECENT_GAMES,
            "players":               snap_records,
        }
        print(f"      {len(snap_records)} rostered offensive players with snap data")

    # ──────────────────────────────────────────────────────────
    # 4) Injury Wire — pull injury_status from the players table
    #    and join to current Huddlepuffers roster ownership.
    # ──────────────────────────────────────────────────────────
    print("[extras_v3] Building injury wire")
    if not DB.exists():
        extras["injury_wire"] = {"available": False}
    else:
        con = sqlite3.connect(str(DB))
        # Pull anyone with a meaningful injury status. "NA" is Sleeper's
        # placeholder for "no current designation" so we exclude it.
        MEANINGFUL = ("Out", "Doubtful", "Questionable", "IR", "PUP",
                      "Sus", "COV", "DNR", "NFI")
        placeholders = ",".join("?" * len(MEANINGFUL))
        cur = con.execute(f"""
            SELECT player_id, full_name, position, team, injury_status, status
            FROM players
            WHERE injury_status IN ({placeholders})
              AND team IS NOT NULL AND team <> ''
              AND position IN ('QB','RB','WR','TE','K','DEF')
        """, MEANINGFUL)
        cols = [d[0] for d in cur.description]
        injury_rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        con.close()

        # Join to current owner from rankings_data players list
        owner_lookup = {p.get("player_id"): p for p in players}
        injuries = []
        for r in injury_rows:
            base = owner_lookup.get(r["player_id"], {})
            injuries.append({
                "player_id":  r["player_id"],
                "full_name":  r["full_name"],
                "position":   r["position"],
                "team":       r["team"],
                "injury_status": r["injury_status"],
                "status":     r["status"],
                "owner_id":   base.get("owner_id"),
                "owner_name": base.get("owner_name") or "FA",
                "rostered":   bool(base.get("rostered")),
                "fc_dyn":     clean_num(base.get("fc_dyn")),
                "is_starter": bool(base.get("is_starter")),
            })

        # Severity rank for sorting
        SEVERITY = {
            "Out": 5, "IR": 5, "PUP": 4, "Sus": 4, "NFI": 4, "DNR": 4,
            "Doubtful": 3, "COV": 3,
            "Questionable": 2,
        }
        for i in injuries:
            i["severity"] = SEVERITY.get(i["injury_status"], 1)
        injuries.sort(key=lambda x: (-x["severity"], -(x["fc_dyn"] or 0)))

        # Per-owner counts for the banner
        owner_counts = defaultdict(lambda: {"total": 0, "starters": 0, "high_value": 0})
        for i in injuries:
            if not i["rostered"] or i["owner_name"] == "FA":
                continue
            o = i["owner_name"]
            owner_counts[o]["total"] += 1
            if i["is_starter"]:
                owner_counts[o]["starters"] += 1
            if (i["fc_dyn"] or 0) >= 3000:
                owner_counts[o]["high_value"] += 1

        extras["injury_wire"] = {
            "available":     True,
            "injuries":      injuries,
            "owner_counts":  dict(owner_counts),
            "total":         len(injuries),
            "rostered_total": sum(1 for i in injuries if i["rostered"]),
        }
        print(f"      {len(injuries)} injuries · {sum(1 for i in injuries if i['rostered'])} on rosters · "
              f"{len(owner_counts)} owners affected")

    # ──────────────────────────────────────────────────────────
    # 5) Strength of Schedule for the upcoming draft season (proxy)
    #    DvP rankings from the LAST_COMPLETE_SEASON + each team's CURRENT_SEASON
    #    schedule, used as a proxy until the next-season schedule drops.
    # ──────────────────────────────────────────────────────────
    dvp_season = config.LAST_COMPLETE_SEASON
    sched_season = config.CURRENT_SEASON
    target_sos_season = config.NEXT_DRAFT_SEASON
    print(f"[extras_v3] Building {target_sos_season} SoS ({dvp_season} DvP × {sched_season} schedule proxy)")
    if not DB.exists():
        extras["sos"] = {"available": False}
    else:
        con = sqlite3.connect(str(DB))

        # 1. Defense vs Position from LAST_COMPLETE_SEASON — points allowed per game
        cur = con.execute("""
            SELECT opponent_team AS def_team,
                   position,
                   SUM(COALESCE(fantasy_points_ppr, 0))         AS pts,
                   COUNT(DISTINCT season || '_' || week)        AS games
            FROM nfl_weekly_stats
            WHERE season = ? AND season_type = 'REG'
              AND opponent_team IS NOT NULL AND opponent_team <> ''
              AND position IN ('QB','RB','WR','TE')
            GROUP BY opponent_team, position
        """, (dvp_season,))
        cols = [d[0] for d in cur.description]
        dvp_rows = [dict(zip(cols, r)) for r in cur.fetchall()]

        # ppr per game allowed
        for r in dvp_rows:
            r["ppr_per_game"] = round(r["pts"] / max(r["games"], 1), 1)

        # 2. Team's CURRENT_SEASON schedule (used as next-season proxy)
        cur = con.execute("""
            SELECT DISTINCT week, team, opponent
            FROM nfl_snap_counts
            WHERE season = ? AND game_type = 'REG'
              AND team IS NOT NULL AND opponent IS NOT NULL
            ORDER BY team, week
        """, (sched_season,))
        sched_rows = [{"week": r[0], "team": r[1], "opp": r[2]} for r in cur.fetchall()]
        con.close()

        # Build dvp lookup: (def_team, pos) -> ppr_per_game
        dvp_lookup = {}
        for r in dvp_rows:
            dvp_lookup[(r["def_team"], r["position"])] = r["ppr_per_game"]

        # Rank 1..32 PER POSITION (1 = TOUGHEST defense — least pts allowed)
        positions = ["QB", "RB", "WR", "TE"]
        dvp_rank = {}  # (def_team, pos) -> rank
        ranks_per_pos = {}  # pos -> sorted list of (team, ppr_per_game, rank)
        for pos in positions:
            ordered = sorted(
                ((t, p) for (t, p) in dvp_lookup if p == pos),
                key=lambda k: dvp_lookup[k]
            )
            ranks_per_pos[pos] = []
            for rank, (team, p) in enumerate(ordered, start=1):
                dvp_rank[(team, pos)] = rank
                ranks_per_pos[pos].append({
                    "team": team, "ppr_per_game": dvp_lookup[(team, p)], "rank": rank
                })

        # 3. For each team, aggregate avg opponent DvP rank by position
        team_schedule = defaultdict(list)  # team -> list of opponents
        for s in sched_rows:
            team_schedule[s["team"]].append(s["opp"])

        team_sos = []
        for team, opps in sorted(team_schedule.items()):
            entry = {"team": team, "games": len(opps), "opponents": opps}
            for pos in positions:
                ranks = [dvp_rank.get((opp, pos)) for opp in opps]
                ranks = [r for r in ranks if r is not None]
                if ranks:
                    avg = sum(ranks) / len(ranks)
                    entry[f"sos_{pos}_avg_rank"] = round(avg, 1)
                else:
                    entry[f"sos_{pos}_avg_rank"] = None
            team_sos.append(entry)

        # Rank 1..32 on each team's SoS per position (1 = EASIEST schedule = highest opp rank avg)
        # Higher avg opp rank means opponents are weaker defenses (1=tough) → high avg = soft schedule
        for pos in positions:
            ordered = sorted(
                team_sos, key=lambda t: -(t.get(f"sos_{pos}_avg_rank") or 0)
            )
            for i, t in enumerate(ordered, start=1):
                t[f"sos_{pos}_rank"] = i  # 1 = easiest schedule for this position

        # 4. Aggregate per Huddlepuffers roster — sum each player's team's
        #    SoS rank for that player's position
        owner_agg = defaultdict(lambda: {
            p: {"sum_rank": 0, "count": 0} for p in positions
        })
        for p in players:
            if not p.get("rostered") or p.get("owner_name") in (None, "FA"):
                continue
            pos = p.get("position")
            if pos not in positions:
                continue
            team = p.get("team")
            if not team:
                continue
            sos = next((t for t in team_sos if t["team"] == team), None)
            if not sos:
                continue
            r = sos.get(f"sos_{pos}_rank")
            if r is None:
                continue
            o = p.get("owner_name")
            owner_agg[o][pos]["sum_rank"] += r
            owner_agg[o][pos]["count"] += 1

        roster_sos = []
        for owner, pos_dict in owner_agg.items():
            entry = {"owner_name": owner}
            overall_sum, overall_n = 0, 0
            for pos in positions:
                pd_ = pos_dict[pos]
                avg = round(pd_["sum_rank"] / pd_["count"], 1) if pd_["count"] else None
                entry[f"{pos}_avg_rank"] = avg
                entry[f"{pos}_n"] = pd_["count"]
                overall_sum += pd_["sum_rank"]
                overall_n += pd_["count"]
            entry["overall_avg_rank"] = round(overall_sum / overall_n, 1) if overall_n else None
            roster_sos.append(entry)
        roster_sos.sort(key=lambda r: -(r["overall_avg_rank"] or 0))

        extras["sos"] = {
            "available":      True,
            "dvp_season":     dvp_season,
            "schedule_season": sched_season,
            "schedule_label": f"{sched_season} schedule used as {target_sos_season} proxy (NFL releases {target_sos_season} schedule mid-May)",
            "positions":      positions,
            "dvp":            ranks_per_pos,    # for each position, every team's pts allowed and rank
            "team_sos":       team_sos,         # per team, schedule difficulty 1..32 per pos
            "roster_sos":     roster_sos,       # per owner, aggregated
        }
        print(f"      DvP season: {dvp_season} · schedule: {sched_season} (proxy)")
        print(f"      {len(team_sos)} teams scored · {len(roster_sos)} {config.LEAGUE_NAME_FILTER} rosters aggregated")

    # ──────────────────────────────────────────────────────────
    # 6) Hall of Fame — championship banners, toilet bowl, all-time records.
    #    Built entirely from the dynasty chain already in SQLite
    #    (leagues / rosters / users / matchups / brackets).
    #
    #    League rules encoded here (confirmed by Nick 2026-08-09):
    #    - Champion = winner of the winners_bracket p==1 game.
    #    - Toilet bowl = the 4 non-playoff teams, RANKED BY regular-season
    #      points (fewest = toilet bowl loser = next year's 1.01).
    # ──────────────────────────────────────────────────────────
    print("[extras_v3] Building hall of fame")
    if not DB.exists():
        extras["hall_of_fame"] = {"available": False}
    else:
        extras["hall_of_fame"] = build_hall_of_fame()
        hof = extras["hall_of_fame"]
        print(f"      seasons with banners: {len(hof.get('seasons', []))} · "
              f"franchises: {len(hof.get('franchises', []))} · "
              f"records: {len(hof.get('records', {}))}")

    # ──────────────────────────────────────────────────────────
    # 7) Persist
    # ──────────────────────────────────────────────────────────
    extras["v3_generated_at"] = datetime.utcnow().isoformat() + "Z"

    with open(RANKINGS_JSON, "w") as f:
        json.dump(data, f, default=str)
    print(f"[extras_v3] Wrote {RANKINGS_JSON} ({os.path.getsize(RANKINGS_JSON):,} bytes)")


if __name__ == "__main__":
    main()
