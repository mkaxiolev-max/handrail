# NS∞ Mac App Wrap Audit
**Date:** 2026-04-17 | **Auditor:** claude-sonnet-4-6

---

## Frontend

| Property | Value |
|----------|-------|
| Framework | Vite 4.x + React 18 |
| Package manager | npm |
| Build command | `npm run build` (vite build) |
| Dev command | `vite --port 3000` |
| Output dir | `frontend/dist/` |
| Build result | ✅ builds cleanly in 427ms — 105 modules |
| Build output | `dist/index.html` + `dist/assets/index-0fa12329.js` (243KB) + CSS |

### API URL pattern
All API calls are **absolute localhost** — no relative paths, no env-var injection needed:
```
http://127.0.0.1:9000/system/now
http://127.0.0.1:9000/api/organism/overview
http://127.0.0.1:9000/feed
http://127.0.0.1:9000/feed/build
http://127.0.0.1:9000/intent/execute
http://127.0.0.1:9001/atoms
http://localhost:9000/api/v1/omega
```
These URLs work identically from a Tauri WKWebView. No changes to frontend source required.

### Vite dev proxy
`vite.config.js` has a `/api` → `http://127.0.0.1:9000` proxy, but it is dev-server-only.
The built static assets call APIs directly — proxy is irrelevant at runtime.

### Routes
```
/           → /briefing  (redirect)
/briefing   BriefingPage — live feed, system state
/engine     EnginePage
/runtime    RuntimePage
/organism   OrganismPage  ← best founder surface, calls /api/organism/overview
/governance GovernancePage
/memory     MemoryPage
/calls      CallsPage
/build      BuildPage
/omega      OmegaPage
/violet     VioletPage
```

### Secondary frontend (ns_ui/)
Next.js 16 app in `ns_ui/`. Not used for wrapping — Vite/React in `frontend/` is the correct target.

---

## Toolchain

| Tool | Version | Status |
|------|---------|--------|
| node | v25.2.1 | ✅ |
| npm | 11.6.2 | ✅ |
| cargo | 1.92.0 | ✅ |
| rustup toolchain | stable-aarch64-apple-darwin | ✅ |
| clang | 17.0.0 (Apple CLT) | ✅ |
| swift | 6.2.3 (Apple CLT) | ✅ |
| Tauri CLI | not installed (npm installable @2.10.1) | ready |

---

## Existing wrapper work

| Item | Present | Notes |
|------|---------|-------|
| `apps/NS Infinity.app` | ✅ | AppleScript wrapper — opens Terminal boot script |
| `launchd/com.axiolev.ns_founder_boot.plist` | ✅ | LaunchAgent for boot-helper-at-login |
| `scripts/boot/ns_boot_founder.command` | ✅ | Full idempotent boot script |
| `apps/NS Infinity.app/Contents/Resources/applet.icns` | ✅ | Reusable icon |
| `apps/ns-tauri/` | ❌ | Does not exist yet — to be created |
| Any Tauri/Electron config | ❌ | None present |

---

## Conclusion
Tauri is the right path. No blockers.
