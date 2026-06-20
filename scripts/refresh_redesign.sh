#!/bin/bash
# refresh_redesign.sh — weekly refresh of the REDESIGNED Huddlepuffers dashboard.
#
#   [1] Pull fresh data (reuses the existing pipeline; deploy + old-HTML copy skipped)
#         -> platform/rankings_data.json
#   [2] Inject data + platform/ai_labels.json into platform/redesign_template.html
#         -> platform/index.html   (via scripts/build_redesign.py)
#   [3] Deploy platform/ to Netlify        (skip with REDESIGN_SKIP_DEPLOY=1)
#
# AI labels (platform/ai_labels.json) are the fun copy Claude writes each week.
# This script does NOT regenerate them — if you want fresh nicknames/blurbs/recap,
# have Claude rewrite ai_labels.json *between* steps [1] and [2]. If the file is
# absent/stale, the dashboard falls back to its built-in stat templates.
#
# Usage:
#   bash scripts/refresh_redesign.sh                    # data + build + deploy
#   REDESIGN_SKIP_DEPLOY=1 bash scripts/refresh_redesign.sh   # data + build, no deploy (dry run)
set -u
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT" || { echo "project root missing"; exit 1; }

# Deploy DISABLED locally — the live site is published by GitHub Actions
# (.github/workflows/refresh.yml). Force the skip so a local run rebuilds
# platform/index.html for preview but never publishes (avoids racing the Action).
REDESIGN_SKIP_DEPLOY=1

echo "=== [1/3] Refreshing data (SKIP_DEPLOY=1) ==="
SKIP_DEPLOY=1 bash scripts/refresh_platform.sh \
  || echo "!!! data refresh reported issues — continuing with the rankings_data.json already on disk"

echo "=== [2/3] Building redesign index.html ==="
python3 scripts/build_redesign.py || { echo "build_redesign.py FAILED — aborting before deploy"; exit 1; }

if [ "${REDESIGN_SKIP_DEPLOY:-0}" = "1" ]; then
  echo "=== [3/3] Deploy skipped (REDESIGN_SKIP_DEPLOY=1) ==="
  echo "Dry run complete. platform/index.html is built but not published."
  exit 0
fi

echo "=== [3/3] Deploying to Netlify ==="
cd platform && netlify deploy --prod --dir=. --message="Weekly redesign refresh $(date +%Y-%m-%d)"
