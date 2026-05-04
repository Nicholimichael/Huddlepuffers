# Fantasy Football — Huddlepuffers Data Project

A personal data warehouse for the **Huddlepuffers** Sleeper Dynasty league, plus NFL player performance data, built for trade analysis, roster management, and dynasty strategy.

## Folder layout

```
Fantasy Football/
├── README.md                ← you are here
├── scripts/
│   ├── fetch_sleeper.py     ← pulls Huddlepuffers league history from Sleeper API
│   ├── fetch_fantasycalc.py ← pulls dynasty trade values from FantasyCalc
│   ├── fetch_nfl_stats.py   ← pulls NFL weekly/seasonal stats via nfl-data-py
│   ├── analyze_roster.py    ← scores your roster + league valuations + buy-low list
│   ├── refresh.sh           ← runs all pulls + analysis in sequence
│   └── requirements.txt     ← python deps
├── data/
│   ├── raw/                 ← raw JSON responses (for reprocessing)
│   └── csv/                 ← flat CSVs you can open in Excel
└── db/
    └── fantasy.sqlite       ← unified SQLite database for SQL querying
```

## One-time setup

Open Terminal and run:

```bash
cd "/Users/Consulting/Documents/Claude/Projects/Fantasy Football/scripts"
pip3 install -r requirements.txt
```

## Pulling data

**Pull everything (Sleeper + NFL stats):**
```bash
cd "/Users/Consulting/Documents/Claude/Projects/Fantasy Football/scripts"
./refresh.sh
```

**Pull just Sleeper (faster):**
```bash
python3 fetch_sleeper.py
```

**Pull just NFL stats:**
```bash
python3 fetch_nfl_stats.py
```

The Sleeper pull takes ~30–90 seconds depending on how many seasons of league history exist. NFL stats pull takes 1–3 minutes (downloads weekly stats, snap counts, Next Gen Stats).

## What gets pulled

### From Sleeper (Huddlepuffers)
| Table / CSV | Description |
|---|---|
| `leagues` | One row per season of Huddlepuffers (follows the dynasty chain via `previous_league_id`) |
| `users` | League members for each season |
| `rosters` | Team-level roster info (record, points, division, settings) |
| `roster_players` | One row per player per roster (with starter / taxi / reserve flags) |
| `matchups` | Weekly matchup scores per roster (regular season + playoffs) |
| `transactions` | Trades, waivers, free agent adds, commissioner moves |
| `drafts` | Draft metadata per season |
| `draft_picks` | Every draft pick across all years |
| `traded_picks` | All future-pick trades — critical for dynasty draft capital tracking |
| `players` | Full Sleeper NFL player database (~7,000 players with positions, teams, age, status) |
| `nfl_state` | Current NFL week/season pointer |

### From nfl-data-py
| Table / CSV | Description |
|---|---|
| `nfl_weekly_stats` | Weekly per-player stats (passing, rushing, receiving, fantasy points) |
| `nfl_seasonal_stats` | Season-aggregated per-player stats |
| `nfl_rosters` | NFL rosters by season (with gsis_id for joining) |
| `nfl_player_ids` | ID crosswalk: `sleeper_id` ↔ `gsis_id` ↔ `pfr_id` ↔ `espn_id` etc. — joins Sleeper to NFL data |
| `nfl_snap_counts` | Snap counts by week (offense / defense / special teams %) |
| `nfl_ngs_passing` | Next Gen Stats for QBs (CPOE, time to throw, aggressiveness, etc.) |
| `nfl_ngs_rushing` | Next Gen Stats for RBs (efficiency, expected yards, time behind LOS) |
| `nfl_ngs_receiving` | Next Gen Stats for WRs/TEs (avg separation, cushion, target share) |

## Joining Sleeper ↔ NFL data

The `nfl_player_ids` table is your bridge. Sleeper's `player_id` field is actually the GSIS ID for most players (e.g. `00-0034796` for Patrick Mahomes), but for non-NFL players (rookies pre-draft, IDP), Sleeper uses its own IDs. Use `nfl_player_ids.sleeper_id` to join cleanly.

Example query (find my current roster's avg target share):
```sql
SELECT p.full_name, p.position, w.targets, w.target_share
FROM roster_players rp
JOIN rosters r ON r.roster_id = rp.roster_id AND r.league_id = rp.league_id
JOIN players p ON p.player_id = rp.player_id
LEFT JOIN nfl_player_ids ids ON ids.sleeper_id = rp.player_id
LEFT JOIN nfl_weekly_stats w ON w.player_id = ids.gsis_id AND w.season = 2025
WHERE r.owner_id = '<my user_id>'
ORDER BY w.target_share DESC;
```

## Configuration

Edit the `CONFIG` block at the top of either script to change:
- `USERNAME` — Sleeper username (default: `nmhochstedler`)
- `LEAGUE_NAME_FILTER` — set to `None` to pull ALL your leagues; default `"Huddlepuffers"`
- `START_SEASON` / `MIN_SEASON` — how far back to walk for league discovery
- `SEASONS` — which NFL seasons to pull stats for

## Refresh cadence

- **Daily** during the season: `./refresh.sh` to keep matchups, transactions, and weekly stats current
- **Weekly** in the offseason: enough to catch traded picks and roster moves
- **One-time** at season end: archive the season's data before rosters reset

## Future data sources to add

- **FantasyCalc** dynasty trade values (`https://api.fantasycalc.com/values/current`) — public JSON
- **KeepTradeCut** dynasty rankings — scrape friendly
- **DynastyProcess** — open CSV repo on GitHub
- **FantasyPros ECR** — consensus rankings
- **PFR advanced stats** — historical advanced metrics

## Notes on running inside Cowork

The Cowork sandbox blocks `api.sleeper.app` by default (allowlist). To let Claude run these scripts directly here next session, add `api.sleeper.app` and `github.com` (already allowed) to **Settings → Capabilities → Network allowlist**. Alternatively, just run `./refresh.sh` from your Terminal — it works the same either way.

---
*Last updated: 2026-04-20*
