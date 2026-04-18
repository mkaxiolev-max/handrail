# NS∞ Mac Operator Guide
AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED

---

## Launch by click

**Double-click on Desktop:**
```
~/Desktop/NS∞ Launch.command
```
Terminal opens, services come up, summary prints, browser tabs open.

**Or double-click the app:**
```
~/axiolev_runtime/apps/NS Infinity.app
```

---

## Auto-start at login

The LaunchAgent `com.axiolev.ns_founder_boot` is installed and active.
NS∞ boots automatically on login — no action needed.

**Verify it is loaded:**
```bash
launchctl list | grep axiolev.ns_founder_boot
```
Expect a line with the label and a PID.

**Disable auto-start (temporary):**
```bash
launchctl unload ~/Library/LaunchAgents/com.axiolev.ns_founder_boot.plist
```

**Re-enable:**
```bash
launchctl load ~/Library/LaunchAgents/com.axiolev.ns_founder_boot.plist
```

**Remove permanently:**
```bash
launchctl unload ~/Library/LaunchAgents/com.axiolev.ns_founder_boot.plist
rm ~/Library/LaunchAgents/com.axiolev.ns_founder_boot.plist
```

---

## Before shutdown

Run the verify + save script — it will print exactly one line if ready:
```
Safe to shut down Mac.
```

**Double-click:**
```
~/axiolev_runtime/scripts/boot/ns_verify_and_save.command
```

**Or from terminal:**
```bash
bash ~/axiolev_runtime/scripts/boot/ns_verify_and_save.command
```

If you want a full shutdown record with a markdown summary:
```bash
bash ~/axiolev_runtime/scripts/boot/ns_shutdown_prep.command
```
This writes `artifacts/final_shutdown_prep_<timestamp>.md`.

---

## Log locations

| What | Path |
|------|------|
| Boot stdout | `~/Library/Logs/com.axiolev.ns_founder_boot.log` |
| Boot stderr | `~/Library/Logs/com.axiolev.ns_founder_boot.err.log` |
| state_api | `/tmp/ns_state_api.log` |
| Verify artifacts | `~/axiolev_runtime/artifacts/verify_<timestamp>.json` |
| Shutdown records | `~/axiolev_runtime/artifacts/final_shutdown_prep_<timestamp>.md` |

---

## All operator scripts

| Script | Purpose |
|--------|---------|
| `scripts/boot/ns_boot_founder.command` | Full boot — services + UI |
| `scripts/boot/ns_verify_and_save.command` | Verify + write artifact |
| `scripts/boot/ns_shutdown_prep.command` | Verify + safe shutdown record |
| `apps/NS Infinity.app` | Clickable macOS app (opens boot in Terminal) |
| `~/Desktop/NS∞ Launch.command` | Desktop shortcut → boot script |
| `launchd/com.axiolev.ns_founder_boot.plist` | LaunchAgent source |
