# NATIVE_UI_PATH_DECISION — NS∞ macOS Habitat

**Date**: 2026-04-21

---

## Canonical Native App Target

**`apps/ns_mac/NSInfinityApp/NSInfinityApp.xcodeproj`**

This is the one canonical native path. All future macOS native development happens here.

## Existing Shells — Decision

| Shell | Decision | Rationale |
|-------|----------|-----------|
| `services/mobile/NSInfinity/` | **Seed reference only** — do not delete, do not develop further | 5-view TabView with basic NSClient. Useful as data contract seed. Not founder habitat. |
| `apps/ns-tauri/` | **Legacy reference** — do not develop further | Tauri wrapper around web UI. Remains as reference for web IA. |
| `apps/NS Infinity.app/` | **Built artifact** — leave as-is | Tauri build output. Not a source tree. |

## Data Plane

The native app consumes the live NS∞ runtime via:

| Endpoint | Role |
|----------|------|
| `http://localhost:9000` | NS primary — health, memory, intel, voice, scoring |
| `http://localhost:8011` | Handrail — CPS execution |
| `http://localhost:8788` | Continuum — state, events, receipts |

No fake data in the main path. Offline state is shown explicitly as "services offline."

## Web Surfaces — Temporary References Only

The Tauri/web UI and any HTML replicas are:
- Migration reference for information architecture
- Data contract reference for endpoint shapes
- NOT peers to the native app
- NOT upgraded in this pass

## Architecture Decision Record

> The canonical NS∞ founder habitat is a native macOS application built with SwiftUI + AppKit + Metal, consuming the existing runtime as truth. The web shell is retired as the primary surface. The Swift Package at `services/mobile/` is superseded but preserved as a development seed.
