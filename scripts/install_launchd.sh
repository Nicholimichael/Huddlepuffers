#!/bin/bash
# install_launchd.sh — Installs the Huddlepuffers weekly refresh LaunchAgent.
#
# Run this ONCE from your Terminal:
#   cd "/Users/Consulting/Documents/Claude/Projects/Fantasy Football/scripts"
#   ./install_launchd.sh
#
# After install: macOS will run refresh_platform.sh every Wednesday at 7:00 AM
# local time (automatically, even when Cowork / Claude is closed). If the Mac
# is asleep at 7 AM, the job fires at next wake.

set -e

PROJECT_ROOT="/Users/Consulting/Documents/Claude/Projects/Fantasy Football"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"
PLIST_SRC="$SCRIPTS_DIR/com.hossautomation.huddlepuffers-refresh.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.hossautomation.huddlepuffers-refresh.plist"

if [ ! -f "$PLIST_SRC" ]; then
  echo "ERROR: $PLIST_SRC not found"
  exit 1
fi

mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$HOME/Library/LaunchAgents"

# Make sure the refresh script is executable
chmod +x "$SCRIPTS_DIR/refresh_platform.sh"
chmod +x "$SCRIPTS_DIR/refresh.sh" 2>/dev/null || true

# If already loaded, unload first so we pick up any plist changes
if launchctl list | grep -q "com.hossautomation.huddlepuffers-refresh"; then
  echo "Unloading existing LaunchAgent..."
  launchctl unload "$PLIST_DEST" 2>/dev/null || true
fi

echo "Copying plist → $PLIST_DEST"
cp "$PLIST_SRC" "$PLIST_DEST"

echo "Loading LaunchAgent..."
launchctl load "$PLIST_DEST"

echo ""
echo "✓ Installed. Verification:"
launchctl list | grep huddlepuffers || echo "  (not listed yet — may take a moment)"

echo ""
echo "Next run: Wednesday 7:00 AM local"
echo "Logs:     $PROJECT_ROOT/logs/launchd_out.log"
echo "          $PROJECT_ROOT/logs/launchd_err.log"
echo ""
echo "To trigger a test run NOW:"
echo "  launchctl start com.hossautomation.huddlepuffers-refresh"
echo ""
echo "To disable (pause weekly runs):"
echo "  launchctl unload $PLIST_DEST"
echo ""
echo "To uninstall completely:"
echo "  launchctl unload $PLIST_DEST && rm $PLIST_DEST"
