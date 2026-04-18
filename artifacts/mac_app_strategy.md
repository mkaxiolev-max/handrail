# NS∞ Mac App Wrapper Strategy
**Date:** 2026-04-17

---

## Decision: TAURI v2

### Rationale

**All three Tauri feasibility conditions met:**

1. **Frontend can build to static assets** ✅  
   Vite 4 + React 18. `npm run build` → `frontend/dist/` in 427ms. No SSR, no server-side rendering needed.

2. **Local APIs reachable from native webview** ✅  
   All API calls are absolute `http://127.0.0.1:9000/...` — identical behaviour from Tauri WKWebView as from browser. No CORS issues (backend is local). No changes to frontend source required.

3. **Launching local services before showing UI is possible** ✅  
   Rust `main.rs` spawns `apps/ns_tauri_boot.sh` (lightweight service check) before the window is shown. The boot script calls the existing `docker compose up -d` and state_api start logic.

### Why NOT Electron
- Cargo + Rust already installed — Tauri has no extra runtime overhead
- Tauri produces ~20MB `.app`; Electron would be ~150MB+
- Tauri WKWebView on macOS is identical to Safari's engine — no Chromium bundle needed
- Electron would add a dependency for no benefit

---

## App structure

```
apps/ns-tauri/
├── package.json                  # @tauri-apps/cli dev dep
├── src-tauri/
│   ├── Cargo.toml
│   ├── build.rs
│   ├── tauri.conf.json           # productName, window, CSP, bundle
│   ├── icons/
│   │   └── icon.icns             # copied from existing applet.icns
│   └── src/
│       └── main.rs               # Alexandria check + boot spawn + tauri::Builder
```

## Boot integration

1. App launches (double-click or login)
2. Rust `main.rs`:
   - Checks `/Volumes/NSExternal` → if absent: osascript dialog + exit(1)
   - Spawns `apps/ns_tauri_boot.sh` non-blocking (brings up Docker + state_api)
3. Main window loads `frontend/dist/index.html` immediately
4. Frontend's `SystemContext.jsx` polls `http://127.0.0.1:9000/system/now` every 5s
5. Services finish booting in background; UI transitions from error state to live state automatically

## Default route
`/organism` — OrganismPage is the richest founder surface. App opens there.

## Signing status
Unsigned. `codesign --deep --force --sign -` (ad-hoc) applied so macOS Gatekeeper allows local launch with Ctrl+click → Open, or after adding to Security & Privacy.

## Build output
`apps/ns-tauri/src-tauri/target/release/bundle/macos/NS Infinity.app`
