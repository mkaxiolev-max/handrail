# NATIVE_UI_MAPPING — Web Replica → Native Shell

**Date**: 2026-04-21

---

## Shell Regions

| Web/Replica Region | Native Component | File | Status |
|-------------------|-----------------|------|--------|
| Top HUD | `TopBar` | `Shell/TopBar.swift` | ✅ Preserved |
| Left rail / mode nav | `LeftRail` | `Shell/LeftRail.swift` | ✅ Preserved |
| Center organism canvas | `CenterCanvas` → `LivingArchitectureView` | `Shell/CenterCanvas.swift` | ✅ Upgraded (Metal) |
| Right panel / inspector | `RightInspector` | `Shell/RightInspector.swift` | ✅ Preserved |
| Bottom timeline / receipts | `BottomTimeline` | `Shell/BottomTimeline.swift` | ✅ Preserved |
| Voice overlay | `VoiceOverlay` | `Shell/VoiceOverlay.swift` | ✅ Omnipresent ZStack |

## Top HUD — Preserved Exactly

| Web element | Native element |
|-------------|---------------|
| Brand "NS∞" | Text + violet color |
| Current mode label | `appState.currentMode.rawValue` |
| Docker pill | HUDPill — live from HealthPoller |
| Invariants pill | HUDPill — static HELD |
| Ring status pill | HUDPill — 4/5 |
| YubiKey pill | HUDPill — SLOT-1 |
| Shalom pill | HUDPill — ✓ |
| Score badge | ScoreBadge — live from RuntimeAPIClient |

## Left Rail — Preserved Exactly

| Web element | Native element |
|-------------|---------------|
| Mode navigation items | `ModeNavItem` × 6 |
| Service status dots | `ServiceStatusRow` × 6 |
| Founder identity block | `FounderIdentityBlock` |

## Center Canvas — Upgraded

| Web element | Native element | Delta |
|-------------|---------------|-------|
| SVG organism map | Metal MTKView `OrganismRenderer` | Upgraded: real-time GPU render |
| Node circles | Circle primitives in Metal | Same topology, animated |
| Link lines | Quad-based line primitives | Same connections |
| Node labels | SwiftUI `NodeLabel` overlay | Same labels, better typography |
| Node selection | `onNodeSelected` callback | Same, now native responder |

## Right Inspector — Preserved

| Web element | Native element |
|-------------|---------------|
| Violet identity | `InspectorSection("VIOLET")` |
| Score / chamber scores | `InspectorSection("SCORE")` + `ScoreProgressBar` |
| Ring status | `InspectorSection("RINGS")` + `RingRow` |
| Ring 5 gates | `InspectorSection("RING 5 GATES")` + `Ring5Gate` |
| Alexandria summary | `InspectorSection("ALEXANDRIA")` + `AlexandriaSummaryWidget` |

## Modes — All Preserved

| Mode | Native view | Status |
|------|-------------|--------|
| Founder Home | `FounderHomeView` | ✅ Full implementation |
| Living Architecture | `LivingArchitectureView` + Metal | ✅ Full implementation |
| Engine Room | `EngineRoomView` | ✅ Full implementation |
| Alexandria | `AlexandriaView` | ✅ Full implementation |
| Governance | `GovernanceView` | ✅ Full implementation |
| Build Space | `BuildSpaceView` | ✅ Stub (gated on Ring 5) |

## Voice — Upgraded to Omnipresent Overlay

| Web element | Native element | Delta |
|-------------|---------------|-------|
| Voice tab/page | `VoiceOverlay` ZStack over entire shell | Upgraded: no longer a page |
| Voice state indicator | `VoiceOrb` with animated pulse ring | Upgraded: GPU-animated |
| Voice states | dormant/ready/listening/processing/responding/muted | Same |

## What is Deferred

| Item | Reason |
|------|--------|
| Xcode Previews | Require connected runtime for meaningful preview |
| Push notifications | Ring 5 / production keys not yet live |
| Full Metal 3D organism | Deferred — 2D/2.5D first pass is correct start |
| MetalFX upscaling | Phase 0 hook exists — not activated yet |
| TestFlight / signing | Ring 5 prerequisite |
