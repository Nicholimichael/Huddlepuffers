#!/bin/bash
# Refresh all Huddlepuffers data sources and run the roster analyzer.
# Tolerant: if one step fails, subsequent steps still run.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

run_step() {
  local name="$1"
  local cmd="$2"
  echo ""
  echo "=== $name ==="
  if eval "$cmd"; then
    echo "--- $name OK ---"
  else
    echo "!!! $name FAILED (continuing) !!!"
  fi
}

run_step "[1/4] Pulling Sleeper (Huddlepuffers)" "python3 fetch_sleeper.py"
run_step "[2/4] Pulling FantasyCalc dynasty values" "python3 fetch_fantasycalc.py"
run_step "[3/4] Pulling nfl-data-py stats" "python3 fetch_nfl_stats.py"
run_step "[4/4] Running roster analysis" "python3 analyze_roster.py"

echo ""
echo "=== Refresh complete ==="
