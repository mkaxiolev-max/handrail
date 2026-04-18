# NS∞ Mac App — Founder Reference

AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED

---

## Where the app bundle lives

**Built app:**
```
apps/ns-tauri/src-tauri/target/release/bundle/macos/NS Infinity.app
```

**Convenience alias (post-build):**
```
apps/dist/NS Infinity.app       (copy placed here after build)
~/Desktop/NS∞ Tauri.app         (symlink placed here after build)
```

---

## How to launch

**Option 1 — Double-click from Finder:**
```
Double-click:  apps/dist/NS Infinity.app
```
On first launch, macOS Gatekeeper will block an unsigned app.
Ctrl+click → Open → Open to allow it once.
After that, double-click works normally.

**Option 2 — From terminal:**
```bash
open "apps/dist/NS Infinity.app"
```

**Option 3 — Original boot script (still works):**
```bash
bash ~/axiolev_runtime/scripts/boot/ns_boot_founder.command
```

---

## What it boots

When the app launches:
1. **Alexandria check** — if `/Volumes/NSExternal` is not mounted, shows a native error dialog and exits. Connect the drive and relaunch.
2. **Boot helper** — spawns `apps/ns_tauri_boot.sh` in the background:
   - Waits up to 90s for Docker Desktop
   - Runs `docker compose up -d` (idempotent)
   - Starts `state_api.py` if not running
   - Waits for ns_core :9000, state_api :9090, handrail :8011, continuum :8788
3. **Window opens immediately** showing the NS∞ Founder Console (Organism view by default)
4. While services boot in background, the UI shows its normal loading/error state
5. When services are live, the UI populates automatically (polls every 5s)

---

## If Alexandria is not mounted

The app will show a native macOS error dialog:
```
NS∞ cannot start.

Alexandria (/Volumes/NSExternal) is not mounted.

Please connect the NS External drive and relaunch.
```

Then exit. Connect the drive, then relaunch.

---

## Where logs are

| Log | Path |
|-----|------|
| Tauri boot helper | `~/Library/Logs/com.axiolev.ns-tauri-boot.log` |
| LaunchAgent (login auto-start) | `~/Library/Logs/com.axiolev.ns_founder_boot.log` |
| state_api | `/tmp/ns_state_api.log` |

---

## Signing status

**UNSIGNED** — built with ad-hoc codesigning (`codesign --deep --force --sign -`).

macOS will block the first launch with Gatekeeper. To allow:
1. Ctrl+click the app → Open → Open
2. Or: `xattr -cr "apps/dist/NS Infinity.app"`

For distribution or notarization, a paid Apple Developer ID is required.
The existing Foundation cert (if any) covers the LLC but not Apple notarization.

---

## Rebuilding the app

If you change the frontend:
```bash
cd ~/axiolev_runtime/frontend && npm run build
cd ~/axiolev_runtime/apps/ns-tauri && npx tauri build
```

The build takes ~2–5 min after first compile (Rust caches compiled crates).

---

## Login auto-start

The existing LaunchAgent (`com.axiolev.ns_founder_boot`) auto-starts the
**boot helper** at login (not the full Tauri app). This is intentional —
it ensures services are live before you manually launch the app.

To auto-launch the Tauri app at login instead:
```bash
# Unload existing agent first
launchctl unload ~/Library/LaunchAgents/com.axiolev.ns_founder_boot.plist
# Then update the plist ProgramArguments to open the .app bundle
```

See `launchd/com.axiolev.ns_founder_boot.plist` for the current configuration.
