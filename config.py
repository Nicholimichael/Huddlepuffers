"""Shared configuration for the Huddlepuffers dynasty platform.

Single source of truth for league/user identity and key season constants.

When the dynasty rolls into a new season, update CURRENT_SEASON and
CURRENT_LEAGUE_ID here — every build script will pick up the change.

Used by:
  - platform/build_rankings.py
  - platform/build_platform_v2.py
  - platform/build_extras_v3.py
  - platform/build_artifact_v2.py
  - scripts/fetch_sleeper.py
  - scripts/weekly_digest.py
"""
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────
# Project paths (anchor everything to where this file lives)
# ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH      = PROJECT_ROOT / "db" / "fantasy.sqlite"
DATA_DIR     = PROJECT_ROOT / "data"
PLATFORM_DIR = PROJECT_ROOT / "platform"
SCRIPTS_DIR  = PROJECT_ROOT / "scripts"
REPORTS_DIR  = PROJECT_ROOT / "reports"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"

# ──────────────────────────────────────────────────────────────────────
# League identity
# ──────────────────────────────────────────────────────────────────────
LEAGUE_NAME_FILTER  = "Huddlepuffers"          # Sleeper API name filter
LEAGUE_DISPLAY_NAME = "The Huddlepuffers"      # Used in HTML titles, digests

# Update CURRENT_SEASON each year when the dynasty league rolls over.
CURRENT_SEASON      = 2025                     # int — the active Sleeper season
CURRENT_LEAGUE_ID   = "1182393556535246848"    # Sleeper league_id for CURRENT_SEASON

# Derived season constants — usually you don't change these directly.
CURRENT_SEASON_STR    = str(CURRENT_SEASON)
LAST_COMPLETE_SEASON  = CURRENT_SEASON - 1     # for season-aggregate stats / DvP
SNAP_DATA_SEASON      = CURRENT_SEASON         # most recent season w/ snap data
NEXT_DRAFT_SEASON     = CURRENT_SEASON + 1     # incoming rookie class

# ──────────────────────────────────────────────────────────────────────
# User identity ("me" — the platform owner)
# ──────────────────────────────────────────────────────────────────────
SLEEPER_USERNAME  = "nmhochstedler"
MY_USER_ID        = "472596585608376320"
MY_DISPLAY_NAME   = "Nmhochstedler"
MY_ROSTER_ID      = 5  # roster_id within CURRENT_LEAGUE_ID


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────
def active_league_id_from_db(con):
    """Look up the current league_id from the database by CURRENT_SEASON.

    More resilient than the hardcoded CURRENT_LEAGUE_ID — returns whatever's
    in the leagues table for the configured season. Falls back to the constant
    if the lookup fails (e.g., DB not yet populated).
    """
    import pandas as pd
    try:
        row = pd.read_sql(
            "SELECT league_id FROM leagues WHERE season = ?",
            con, params=[CURRENT_SEASON_STR],
        )
        if len(row):
            return row.iloc[0, 0]
    except Exception:
        pass
    return CURRENT_LEAGUE_ID
