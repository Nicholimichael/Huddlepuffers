#!/bin/bash
# refresh_platform.sh — End-to-end refresh of the Huddlepuffers dynasty platform.
#
# What this does:
#   1) Pulls fresh Sleeper + FantasyCalc + NFL data into db/fantasy.sqlite
#   2) Recomputes composite dynasty + win-now rankings
#   3) Regenerates platform/huddlepuffers_platform.html
#
# Exit code is 0 if the final artifact was produced, 1 otherwise.
# Logs everything to logs/refresh_YYYY-MM-DD_HHMMSS.log

set -u  # error on unset vars; but NOT set -e — we want partial progress

PROJECT_ROOT="/Users/Consulting/Documents/Claude/Projects/Fantasy Football"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"
PLATFORM_DIR="$PROJECT_ROOT/platform"
LOG_DIR="$PROJECT_ROOT/logs"

mkdir -p "$LOG_DIR"
STAMP="$(date +%Y-%m-%d_%H%M%S)"
LOG_FILE="$LOG_DIR/refresh_${STAMP}.log"

# Redirect all output to both terminal and log file
exec > >(tee -a "$LOG_FILE") 2>&1

# Source nvm so the netlify CLI (installed via nvm) is on PATH.
# This matters because launchd runs us with a minimal PATH that excludes ~/.nvm.
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

echo "============================================================"
echo " Huddlepuffers Platform Refresh — $(date)"
echo " Log: $LOG_FILE"
echo "============================================================"

run_step() {
  local name="$1"
  local cmd="$2"
  echo ""
  echo "=== $name ==="
  if eval "$cmd"; then
    echo "--- $name OK ---"
    return 0
  else
    echo "!!! $name FAILED (continuing) !!!"
    return 1
  fi
}

# ---- Step 1: pull source data ----
cd "$SCRIPTS_DIR" || { echo "scripts dir missing"; exit 1; }

run_step "[1/5] Pulling Sleeper (Huddlepuffers)"  "python3 fetch_sleeper.py"
run_step "[2/5] Pulling FantasyCalc values"       "python3 fetch_fantasycalc.py"
run_step "[3/5] Pulling nfl-data-py stats"        "python3 fetch_nfl_stats.py"

# ---- Step 2: rebuild the platform ----
cd "$PLATFORM_DIR" || { echo "platform dir missing"; exit 1; }

run_step "[4/8] Rebuilding composite rankings"    "python3 build_rankings.py"
run_step "[5/8] Augmenting with v2 features"      "python3 build_platform_v2.py"
run_step "[6/8] Augmenting with v3 modules"       "python3 build_extras_v3.py"
# Apply manual lineup override (offseason fix — Sleeper's rosters endpoint returns
# the last-played-week starters, not the user's currently-set lineup. This step
# overlays the hand-edited scripts/manual_lineup_override.json so the dashboard
# matches what the user actually has set in Sleeper. No-op if the override file
# is missing. The script lives in scripts/ — NOT platform/ — so Netlify doesn't
# try to publish it to the CDN.)
run_step "[6b/8] Applying manual lineup override" "python3 \"$SCRIPTS_DIR/apply_lineup_override.py\""
FINAL_STATUS=1
if run_step "[7/8] Rebuilding dashboard HTML"     "python3 build_artifact_v2.py"; then
  # Copy generated file from outputs (where the build script writes it) into platform/
  # build_artifact.py writes to /sessions/... in Cowork; running locally it'll write
  # wherever the script is configured. Adjust if/when you run it outside Cowork.
  if [ -f "$PLATFORM_DIR/huddlepuffers_platform.html" ]; then
    FINAL_STATUS=0
  elif [ -f "$PLATFORM_DIR/../outputs/huddlepuffers_platform.html" ]; then
    cp "$PLATFORM_DIR/../outputs/huddlepuffers_platform.html" "$PLATFORM_DIR/"
    FINAL_STATUS=0
  fi
fi

# ---- Step 3: snapshot + week-over-week digest ----
# Copies today's rankings_data.json into data/snapshots/rankings_YYYY-MM-DD.json
# and regenerates reports/weekly_digest_YYYY-MM-DD.md diffing the last two.
cd "$SCRIPTS_DIR" || exit $FINAL_STATUS
run_step "[8/9] Snapshot + weekly digest"         "python3 weekly_digest.py"

# ---- Step 4: deploy to Netlify ----
# Only deploy if the build actually produced a fresh artifact. Never push a broken build.
# Set SKIP_DEPLOY=1 in the environment to bypass deploy (useful for local testing).
DEPLOY_STATUS=1
if [ $FINAL_STATUS -eq 0 ] && [ "${SKIP_DEPLOY:-0}" != "1" ]; then
  cd "$PLATFORM_DIR" || exit $FINAL_STATUS
  # Netlify serves index.html at the root URL — copy the dashboard to that name
  # so https://huddlepuffers.hossautomation.com/ loads it directly.
  cp -f "huddlepuffers_platform.html" "index.html"
  if run_step "[9/9] Deploying to Netlify" \
              "netlify deploy --prod --dir=. --message=\"Auto-refresh ${STAMP}\""; then
    DEPLOY_STATUS=0
  fi
elif [ "${SKIP_DEPLOY:-0}" = "1" ]; then
  echo ""
  echo "=== [9/9] Deploy skipped (SKIP_DEPLOY=1) ==="
  DEPLOY_STATUS=0
fi

echo ""
echo "============================================================"
if [ $FINAL_STATUS -eq 0 ]; then
  SIZE=$(wc -c < "$PLATFORM_DIR/huddlepuffers_platform.html" 2>/dev/null || echo "?")
  if [ $DEPLOY_STATUS -eq 0 ]; then
    echo " ✓ Refresh + deploy complete — huddlepuffers_platform.html ($SIZE bytes)"
    echo " ✓ Live: https://huddlepuffers.hossautomation.com"
  else
    echo " ⚠ Build OK but Netlify deploy FAILED — site still shows previous version"
    echo "   See Netlify error in log above. Manual recovery: cd platform && netlify deploy --prod --dir=."
  fi
else
  echo " ✗ Refresh finished with errors — dashboard may be stale (deploy skipped)"
fi
echo " $(date)"
echo "============================================================"

# Exit 0 only if both build AND deploy succeeded (or deploy was intentionally skipped)
if [ $FINAL_STATUS -eq 0 ] && [ $DEPLOY_STATUS -eq 0 ]; then
  exit 0
else
  exit 1
fi
