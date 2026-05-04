#!/bin/bash
# fix_launchd.sh — Reset and verify the Huddlepuffers weekly-refresh LaunchAgent
# after a TCC / Full Disk Access failure.
#
# WHAT THIS SCRIPT DOES (does NOT do)
# -----------------------------------
# * It DOES: strip macOS quarantine attrs, fix exec bits, bootout/bootstrap the
#   LaunchAgent using modern launchctl, kickstart a test run, and tail the logs.
# * It does NOT: grant Full Disk Access to /bin/bash. That step requires GUI
#   interaction in System Settings — see LAUNCHD_FIX.md, step 1.
#
# RUN THIS FROM Terminal.app (NOT Cowork sandbox):
#   cd "/Users/Consulting/Documents/Claude/Projects/Fantasy Football/scripts"
#   ./fix_launchd.sh

set -u  # unset = error, but don't bail on individual cmd failures (-e off)

PROJECT_ROOT="/Users/Consulting/Documents/Claude/Projects/Fantasy Football"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"
PLIST_SRC="$SCRIPTS_DIR/com.hossautomation.huddlepuffers-refresh.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.hossautomation.huddlepuffers-refresh.plist"
LABEL="com.hossautomation.huddlepuffers-refresh"
LOG_DIR="$PROJECT_ROOT/logs"
UID_NUM="$(id -u)"

echo "============================================================"
echo " Huddlepuffers LaunchAgent fix script"
echo " $(date)"
echo "============================================================"

# ---- pre-flight ----
if [ ! -f "$PLIST_SRC" ]; then
  echo "✗ ERROR: $PLIST_SRC not found"
  exit 1
fi
if [ ! -f "$SCRIPTS_DIR/refresh_platform.sh" ]; then
  echo "✗ ERROR: $SCRIPTS_DIR/refresh_platform.sh not found"
  exit 1
fi

# ---- 1. Clear macOS quarantine attrs (in case files were touched in Cowork sandbox) ----
echo ""
echo "[1/6] Stripping com.apple.quarantine + provenance attrs from scripts..."
for f in "$SCRIPTS_DIR"/*.sh "$SCRIPTS_DIR"/*.py "$SCRIPTS_DIR"/*.plist "$PROJECT_ROOT/platform"/*.py; do
  [ -f "$f" ] || continue
  xattr -d com.apple.quarantine "$f" 2>/dev/null || true
  xattr -d com.apple.provenance "$f" 2>/dev/null || true
done
echo "    done."

# ---- 2. Ensure exec bits ----
echo ""
echo "[2/6] Ensuring exec bits on shell scripts..."
chmod +x "$SCRIPTS_DIR/refresh_platform.sh"
chmod +x "$SCRIPTS_DIR/refresh.sh" 2>/dev/null || true
chmod +x "$SCRIPTS_DIR/install_launchd.sh"
chmod +x "$SCRIPTS_DIR/fix_launchd.sh"
ls -l "$SCRIPTS_DIR"/*.sh

# ---- 3. Bootout existing agent (modern equivalent of launchctl unload) ----
echo ""
echo "[3/6] Booting out any existing LaunchAgent..."
launchctl bootout "gui/$UID_NUM/$LABEL" 2>/dev/null && echo "    booted out." || echo "    (not currently loaded — ok)"

# ---- 4. Re-copy plist + bootstrap ----
echo ""
echo "[4/6] Copying plist + bootstrapping LaunchAgent..."
mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$LOG_DIR"
cp "$PLIST_SRC" "$PLIST_DEST"
plutil -lint "$PLIST_DEST"  # validate plist syntax
launchctl bootstrap "gui/$UID_NUM" "$PLIST_DEST"
BOOTSTRAP_RC=$?
if [ $BOOTSTRAP_RC -ne 0 ]; then
  echo "    ✗ bootstrap failed (rc=$BOOTSTRAP_RC)"
  echo "      most common cause: Full Disk Access not granted to /bin/bash."
  echo "      see LAUNCHD_FIX.md step 1 — then re-run this script."
  exit 1
fi
echo "    ✓ bootstrapped."

# ---- 5. Verify it's listed ----
echo ""
echo "[5/6] Verifying LaunchAgent is registered..."
launchctl print "gui/$UID_NUM/$LABEL" 2>/dev/null | head -25 || \
  echo "    (could not print — check 'launchctl list | grep huddlepuffers')"

# ---- 6. Force-fire a test run + tail logs ----
echo ""
echo "[6/6] Force-firing a test run via kickstart..."
> "$LOG_DIR/launchd_err.log"  # truncate so we see only this run's errors
> "$LOG_DIR/launchd_out.log"
launchctl kickstart -k "gui/$UID_NUM/$LABEL"
KICK_RC=$?
echo "    kickstart rc=$KICK_RC. Sleeping 15s for the job to write logs..."
sleep 15

echo ""
echo "------ launchd_out.log (last 20 lines) ------"
tail -n 20 "$LOG_DIR/launchd_out.log" 2>/dev/null || echo "(empty)"
echo "------ launchd_err.log (last 20 lines) ------"
tail -n 20 "$LOG_DIR/launchd_err.log" 2>/dev/null || echo "(empty)"
echo "------ most recent refresh_*.log ------"
LATEST="$(ls -t "$LOG_DIR"/refresh_*.log 2>/dev/null | head -n 1)"
if [ -n "$LATEST" ]; then
  echo "$LATEST"
  tail -n 25 "$LATEST"
else
  echo "(no refresh_*.log produced — the job did not actually run.)"
fi

echo ""
echo "============================================================"
if grep -q "Operation not permitted" "$LOG_DIR/launchd_err.log" 2>/dev/null; then
  echo " ✗ STILL FAILING with 'Operation not permitted'."
  echo "   You MUST grant Full Disk Access to /bin/bash."
  echo "   See LAUNCHD_FIX.md step 1, then re-run this script."
  exit 2
elif [ -n "$LATEST" ] && grep -q "Refresh complete" "$LATEST" 2>/dev/null; then
  echo " ✓ FIXED. Refresh ran end-to-end."
  echo "   Next scheduled fire: Wednesday at 7:00 AM local."
  exit 0
else
  echo " ⚠ INCONCLUSIVE. The LaunchAgent loaded but the test run didn't"
  echo "   produce a 'Refresh complete' line. Check the logs above."
  exit 3
fi
