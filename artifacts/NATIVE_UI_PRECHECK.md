# NATIVE_UI_PRECHECK — NS∞ macOS Habitat

**Date**: 2026-04-21  
**Branch**: integration/max-omega-20260421-191635  
**HEAD**: e58ac6e5  

---

## Git State

```
branch: integration/max-omega-20260421-191635
HEAD:   e58ac6e5
dirty:  yes — untracked CPI/REALITY_CONTACT artifacts + modified .verify_artifacts
```

## Score (no-tests, NVIR stale)

```
v3.1 = 87.63   (canonical live was 92.27 with NVIR active — services currently down)
I1=88.8  I2=83.8  I3=85.1  I4=89.4  I5=89.7  I6=89.95
```

## Service Health

All 6 ports offline at precheck time (8011 / 8788 / 9000 / 9001 / 9010 / 9011).  
Services are not expected to be running during this native UI build pass.

## Existing Native Shells

| Shell | Path | Status |
|-------|------|--------|
| Swift Package (iOS/macOS) | `services/mobile/NSInfinity/` | Legacy — Package.swift, 5 basic views (Chat, Voice, Memory, Status, ContentView) |
| Tauri app | `apps/ns-tauri/` | Legacy wrapper — Tauri 1.x, web frontend only |
| Built .app bundle | `apps/NS Infinity.app/` | Tauri build artifact — not Xcode project |
| Dist bundle | `apps/dist/NS Infinity.app/` | Same |

## Xcode State

- No `.xcodeproj` or `.xcworkspace` found in repo
- Swift 6.2.3 (swiftlang-6.2.3.3.21) available
- Target: arm64-apple-macosx26.0
- `swift package generate-xcodeproj` command exists (legacy, deprecated)
- No `xcodegen` installed

## ns_ui Build Status

No dedicated `services/ns_ui/` directory. The existing Swift package at `services/mobile/NSInfinity/` is the prior native attempt — minimal (TabView, basic client), not a founder habitat.

## Assessment

| Item | Status |
|------|--------|
| Canonical Swift code | `services/mobile/NSInfinity/` — legacy/seed only |
| Canonical native app target | **DOES NOT EXIST YET** — being created this pass |
| Tauri/web shells | Legacy references only — not upgraded further |
| Xcode project | **BEING CREATED**: `apps/ns_mac/NSInfinityApp/` |

## What This Pass Builds

A real native macOS SwiftUI + AppKit + Metal Xcode project at:

```
apps/ns_mac/NSInfinityApp/
  NSInfinityApp.xcodeproj/
  NSInfinityApp/
    App/          — entry point, AppDelegate
    Shell/        — TopBar, LeftRail, CenterCanvas, RightInspector, BottomTimeline, VoiceOverlay
    Features/     — FounderHome, LivingArchitecture, EngineRoom, Alexandria, Governance, Execution, Omega, Timeline, Scoring, Settings
    Metal/        — MTKView, OrganismRenderer, OrganismShaders.metal
    AppKit/       — WindowManager
    Bridges/      — RuntimeAPIClient, HealthPoller, RuntimeModels
    Models/       — AppState, ServiceHealth
    DesignSystem/ — DSColors, Typography
    Resources/    — Assets.xcassets, Info.plist
```
