# NS∞ Tauri App Verification
**Date:** 2026-04-17 | **Build:** Tauri 2.10.1 / tauri-build 2.5.6 / tauri 2.10.3

---

## Build

| Check | Result |
|-------|--------|
| `tauri build` exit code | 0 |
| Binary path | `apps/ns-tauri/src-tauri/target/release/bundle/macos/NS Infinity.app` |
| Stable copy | `apps/dist/NS Infinity.app` |
| Desktop symlink | `~/Desktop/NS∞ Tauri.app` |
| Architecture | Mach-O thin (arm64) |
| Bundle ID | `com.axiolev.ns-infinity` |
| Codesign | adhoc (flags=0x2) |

## Bundle integrity

| Component | Present |
|-----------|---------|
| `Contents/MacOS/ns-infinity` (Rust binary) | ✅ |
| `Contents/Resources/icon.icns` | ✅ |
| `Contents/Info.plist` | ✅ |
| Frontend assets embedded in binary | ✅ (index.html + /assets/index-*.js + /assets/index-*.css) |
| Alexandria check embedded | ✅ (strings confirm `/Volumes/NSExternal` and osascript dialog) |
| Boot helper path embedded | ✅ (`apps/ns_tauri_boot.sh`) |

## Launch verification

| Check | Result |
|-------|--------|
| App launched (PID confirmed) | ✅ PID 8455 |
| Window title | ✅ "NS∞ Founder Console" (confirmed via AppleScript) |
| Boot helper executed | ✅ |
| Alexandria check: `/Volumes/NSExternal` | ✅ mounted |
| `docker compose up -d` | ✅ completed |
| ns_core :9000 | ✅ live (0s wait) |
| state_api :9090 | ✅ live (0s wait) |
| handrail :8011 | ✅ live (0s wait) |
| continuum :8788 | ✅ live (0s wait) |
| Boot log complete marker | ✅ `ns_tauri_boot complete` |

## Frontend in app

Frontend is served via Tauri's `asset://` protocol from assets embedded at compile time.
All NS∞ API calls (`http://127.0.0.1:9000/...`) are made from the WKWebView directly to local services.
No dev server required. No external dependencies.

## Login auto-start

| Item | Status |
|------|--------|
| `com.axiolev.ns_founder_boot` LaunchAgent | ✅ loaded |
| Strategy | Boot-helper-at-login (not app-at-login) |
| Why | Ensures Docker/services are live before founder opens app; avoids Gatekeeper issues |
| App launch | Manual (double-click) or `open "apps/dist/NS Infinity.app"` |

## Signing status

Ad-hoc signed (`--sign -`). Not notarized. Not developer-ID signed.

**To launch on this Mac:** `xattr -cr "apps/dist/NS Infinity.app"` (one-time), then double-click.
Or: Ctrl+click → Open → Open (Gatekeeper bypass).

## What is NOT done

- Apple Developer ID codesigning (requires paid membership + cert)
- Notarization (requires Developer ID + Apple servers)
- Hardened runtime entitlements (not required for local/founder use)
- Distribution via App Store or DMG (not required)

## Build reproducibility

Subsequent builds: `cd apps/ns-tauri && npx tauri build` (~8s after first compile).
Re-run frontend build first if frontend changed: `cd frontend && npm run build`.
