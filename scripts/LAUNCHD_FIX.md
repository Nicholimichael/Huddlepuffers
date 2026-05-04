# LaunchAgent Fix — "Operation not permitted"

The Wednesday weekly-refresh LaunchAgent has been failing with this error in `logs/launchd_err.log`:

```
shell-init: error retrieving current directory: getcwd: cannot access parent directories: Operation not permitted
/bin/bash: .../scripts/refresh_platform.sh: Operation not permitted
```

This is **macOS TCC (Transparency, Consent, and Control)** blocking `/bin/bash` from reading files inside `~/Documents`. Your project lives at `~/Documents/Claude/Projects/Fantasy Football/` — a TCC-protected location — and the `bash` binary that `launchd` invokes does not have Full Disk Access.

**Two-step fix.** Step 1 is GUI-only (no script can do it for you). Step 2 is the included `fix_launchd.sh`.

---

## Step 1 — Grant Full Disk Access to `/bin/bash` (REQUIRED, GUI-only)

1. Open **System Settings** → **Privacy & Security** → **Full Disk Access**.
2. Click the **+** button (you'll be prompted for your password).
3. In the file picker, press **⌘ + Shift + G** and paste: `/bin/bash`
4. Press Return → click **Open** → make sure the toggle next to `bash` is **ON**.
5. Repeat the +/⌘-Shift-G/`/bin/bash` flow if `bash` already showed up but was toggled off.

> **Note:** Apple does not let you grant Full Disk Access to `launchd` itself (it's system-protected), but granting it to `/bin/bash` is sufficient because the LaunchAgent invokes `/bin/bash` as the program.

**Optional but recommended:** Also add **Terminal.app** (already there for most users) and your text editor.

---

## Step 2 — Run the fix script from Terminal

Open **Terminal.app** (not the Cowork sandbox — Terminal needs FDA, which it has by default).

```bash
cd "/Users/Consulting/Documents/Claude/Projects/Fantasy Football/scripts"
chmod +x fix_launchd.sh
./fix_launchd.sh
```

The script will:

1. Strip macOS quarantine extended attributes from every `.sh`, `.py`, and `.plist` in the project (these get added when files are touched inside the Cowork sandbox and re-synced).
2. Re-set exec bits on shell scripts.
3. `launchctl bootout` any existing copy of the agent.
4. Re-copy the plist into `~/Library/LaunchAgents/`, validate it with `plutil -lint`, and `launchctl bootstrap` it.
5. `launchctl kickstart -k` to force-fire a test run NOW.
6. Tail the logs and tell you whether the run actually completed.

### What you'll see if step 1 worked

```
 ✓ FIXED. Refresh ran end-to-end.
   Next scheduled fire: Wednesday at 7:00 AM local.
```

### What you'll see if step 1 was skipped

```
 ✗ STILL FAILING with 'Operation not permitted'.
   You MUST grant Full Disk Access to /bin/bash.
   See LAUNCHD_FIX.md step 1, then re-run this script.
```

---

## Verifying it's actually scheduled

After `fix_launchd.sh` succeeds, run this to confirm the Wednesday-at-7am calendar entry is registered:

```bash
launchctl print "gui/$(id -u)/com.hossautomation.huddlepuffers-refresh" | grep -A 4 "calendar"
```

You should see something like:

```
calendar = {
  weekday = 3
  hour    = 7
  minute  = 0
}
```

`weekday = 3` is Wednesday in launchd-speak (Sunday = 0).

---

## If the Mac is asleep at 7:00 AM Wednesday

The plist has `RunAtLoad = false`, so a sleeping Mac at 7am will NOT trigger the job at next wake — the missed window is missed. Two options:

- **Option A (zero-config):** Leave Mac awake Tuesday night. Caffeine.app or `caffeinate -dimsu` until 7:30am Wednesday is enough.
- **Option B (modify plist):** Change `<key>RunAtLoad</key><false/>` to `<true/>` so a missed Wednesday fire executes when the Mac next wakes. Trade-off: it'll also fire once when you reboot, which is harmless but produces an extra log.

If you want Option B, edit `com.hossautomation.huddlepuffers-refresh.plist` line 34 and re-run `fix_launchd.sh`.

---

## If the LaunchAgent fix still fails after Step 1 + Step 2

Two known fallbacks:

1. **Move the project out of `~/Documents`.** Anywhere outside `~/Documents`, `~/Downloads`, `~/Desktop`, and the iCloud Drive folder is TCC-unprotected. Example: `~/HossAutomation/Fantasy Football/`. You'll need to update the hardcoded path in `refresh_platform.sh`, `weekly_digest.py`, the plist, and the platform/build_*.py files.

2. **Use a wrapper LaunchAgent that lives in `~/Library/LaunchAgents/`** (which is automatically TCC-allowed). The wrapper does nothing but `exec` the real `refresh_platform.sh`. This adds a layer of indirection but doesn't actually solve the underlying TCC barrier — Step 1 is still required.

Step 1 is the actual fix. The above are only relevant if Apple changes TCC behavior in a future macOS release.

---

*Last updated: 2026-04-27 — created after two consecutive Wednesday LaunchAgent failures (4/15, 4/22) traced to TCC blocking `/bin/bash`. Run `fix_launchd.sh` once before Wednesday 4/29 7:00 AM.*
