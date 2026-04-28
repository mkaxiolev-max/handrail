# NS∞ UI — Current State & Integration Report

**Branch:** `integration/xctest-20260427`  
**Commit:** `63f4f696`  
**Report Date:** 2026-04-27  
**Score:** NS∞ Omega-Prime v3.1 — 97.42 authoritative  
**Test Baseline:** 1,760 pytest / 21 vitest / 9 XCTest — all passing  

---

## 1. UI Application Inventory

### 1.1 `ns_ui/` — Canonical Next.js Habitat (ACTIVE)

| Attribute | Value |
|-----------|-------|
| Framework | Next.js 16.2.2 (App Router) |
| React | 19.2.4 |
| Language | TypeScript |
| Port | 3001 (dev) |
| State | Zustand v5 + TanStack React Query v5 |
| Charts | Recharts v3 + ReactFlow v11 |
| Animation | Framer Motion v12 |
| Icons | Lucide React v1.7 |
| Styling | Tailwind CSS v4 |
| Tests | Vitest v2 + jsdom — **21 passing** |
| Backend | ns_api `:9011`, ns_core `:9000`, handrail `:8011` |

**Route table (ns_ui canonical):**

| Route | Title | Endpoint |
|-------|-------|----------|
| `/home` | Founder Home | `/api/v1/ui/summary` |
| `/living` | Living Architecture | `/api/v1/ui/architecture` |
| `/governance` | Governance + Canon | `/api/v1/ui/governance` |
| `/engine` | Engine Room | `/api/v1/ui/execution` → SSE `/api/v1/engine/live/stream` |
| `/voice` | Violet (Voice) | `/api/v1/ui/voice` |
| `/alexandria` | Alexandria Ledger | `/api/v1/ui/memory` |
| `/build` | Build + Receipts | `/api/v1/ui/build` |
| `/timeline` | Timeline | `/api/v1/ui/timeline` |
| `/scoring` | Scoring v2.1/v3.0 | `/api/v1/ui/scoring` |
| `/omega_logos` | Ω-Logos (I₆) | `/api/v1/ui/omega_logos` |
| `/ring5` | Ring 5 External Gates | `/api/v1/ui/ring5` |
| `/autonomy` | Autonomy Tiers | `/api/v1/ui/autonomy` |
| `/[slug]` | Dynamic section | varies |

**Component registry (ns_ui):**

| Component | Path | Status |
|-----------|------|--------|
| FounderAppShell | `src/components/shell/FounderAppShell.tsx` | present |
| FounderSidebar | `src/components/shell/FounderSidebar.tsx` | present, 11 nav items |
| FounderStatusStrip | `src/components/shell/FounderStatusStrip.tsx` | present |
| Card / GoldRule | `src/components/ui/Card.tsx` | present |
| Metric | `src/components/ui/Metric.tsx` | present |
| Sparkline | `src/components/ui/Sparkline.tsx` | present |
| EngineRoomPage | `src/features/engine/EngineRoomPage.tsx` | present, SSE live |
| ArchitecturePage | `src/features/architecture/ArchitecturePage.tsx` | present |
| FounderHomePage | `src/features/founder/FounderHomePage.tsx` | present |
| VioletPage | `src/features/violet/VioletPage.tsx` | present |

**Design tokens (ns_ui/src/lib/design-tokens.ts):**
```
founder: #FF6B00 | violet: #00D4FF | adjudication: #00FF88
handrail: #00FFFF | alexandria: #FFFF00 | voice: #00CCFF
kernel: #FF3333 | bg: #0A0E27 | textPrimary: #E0E6FF
```

---

### 1.2 `frontend/` — Legacy Vite/React App (SUPERSEDED, not deleted)

| Attribute | Value |
|-----------|-------|
| Framework | Vite 4.4 + React 18.2 |
| Router | react-router-dom v6 |
| State | Zustand v4 |
| HTTP | Axios |
| Status | Built (`dist/` exists). Not canonical. Not test-covered by vitest. |

**Pages present (frontend/src/pages/):**
BriefingPage, BuildPage, CallsPage, EnginePage, GovernancePage, MemoryPage, OmegaPage, OrganismPage, RuntimePage, VioletPage

**Components present (frontend/src/components/):**
FounderShell, LeftNav, OmegaPanel, TimelineRail, TopStatusBar, TruthPanel, VioletChat, VioletRail, VoiceStateIndicator

---

### 1.3 `apps/ns_mac/NSInfinityApp` — SwiftUI Native Mac App (ACTIVE)

| Attribute | Value |
|-----------|-------|
| Language | Swift 5.9 / SwiftUI |
| Min macOS | 13 |
| Rendering | Metal (OrganismRenderer) |
| XCTest bridge | `NSMacTests` → pytest bridge (9 tests passing) |
| Build artifact | `apps/NS Infinity.app` |

**HabitatMode enum (canonical navigation):**

| Mode | Label | Feature View |
|------|-------|-------------|
| `.livingArch` | Living Architecture | `LivingArchitectureView.swift` |
| `.engineRoom` | Engine Room | `EngineRoomView.swift` |
| `.founderHome` | Programs Runtime | `FounderHomeView.swift` |
| `.alexandria` | Memory | `AlexandriaView.swift` |
| `.governance` | Governance | `GovernanceView.swift` |
| `.buildSpace` | Build Space | `BuildSpaceView.swift` |

**Shell components:**
AppShell, BottomTimeline, CenterCanvas, LeftRail, RightInspector, TopBar, VoiceOverlay

**VoiceState enum:** dormant | ready | listening | processing | responding | muted  
**RingStatus:** `.canonical` (static seeds — not yet live-polled)  
**Service health polling:** `HealthPoller` — probes ns_api, ns_core, handrail

---

### 1.4 `apps/ns-tauri/` — Tauri Shell (PRESENT, incomplete)

Cargo.toml + tauri.conf.json present. No frontend source found. Status: **skeleton, not functional.**

---

## 2. Backend API Surface (ns_api :9011)

**FastAPI routers mounted:**

| Router | Prefix | Key Endpoints |
|--------|--------|---------------|
| system | `/api/v1/system` | `/state`, `/timeline` |
| engine | `/api/v1/engine` | `/live`, `/live/stream` (SSE) |
| programs | `/api/v1/programs` | `/` |
| memory | `/api/v1/memory` | `/receipts` |
| governance | `/api/v1/governance` | `/state` |
| replay | `/api/v1/replay` | (present) |
| omega | `/api/v1/omega` | `/healthz`, `/runs`, `/runs/{id}` |
| ui | `/api/v1/ui` | `/summary`, `/scoring`, `/ring5`, `/omega_logos`, `/autonomy`, `/voice`, `/timeline`, `/execution`, `/build`, `/memory`, `/architecture`, `/governance` |

**API aggregation model:** The UI router proxies to ns_core (:9000), handrail (:8011), continuum, omega services. Falls back to static defaults when services are down — this is noted in code as deliberate for founder-home stability.

---

## 3. Services Layer (50+ services)

The following services exist in `services/` and have Python implementations:

**Memory / Truth:**  
`alexandria`, `ether`, `canon`, `atomlex`, `three_realities`, `witness`, `witness_cosign`

**Governance / Constitutional:**  
`aletheion` (v2 — logos_gate, pre_action, canon_readiness), `pap` (PAP Ω v1.0 shadow mode), `dignity_kernel`, `hamiltonian_gate`, `governor`, `governor2`

**Execution / CPS:**  
`handrail`, `cps`, `cps_risk_tiering`, `proof_carrying_execution`, `reversibility_registry`, `continuum`, `ns_continuum`, `action_outcome_loop`, `goal_formation`, `drift_monitor`, `efficiency_ledger`

**Intelligence / Scoring:**  
`prism_omega`, `arms_scoring`, `math_calc`, `noetic`, `omega`, `omega_logos`, `gpx_omega`, `saq`, `self_mod_sandbox`, `judge_ensemble`, `calibration`, `model_router`

**Reality Ingestion:**  
`reality_ingest` — config.json defines source types; routes/ directory present

**Other:**  
`ns_api`, `ns`, `ns_core`, `ns_bridge`, `violet`, `voice_gateway`, `telephony_bridge`, `mobile`, `nvir`, `integrity`, `rci`, `tla_bridge`, `tla_apalache_bridge`, `validator_adapters`, `validators`, `ui_audit`, `replay`, `hormetic`, `robustness`, `resilience`, `conference_orchestrator`, `conftuner`, `apollo`, `selective`, `slsa`, `universal_contract`, `atlas_coverage`, `assurance`

---

## 4. Data Sources — Mocked vs Real

| Surface | Source | Status |
|---------|--------|--------|
| Founder Home score display | `/api/v1/ui/summary` → ns_core | Real, with fallback defaults |
| Scoring table (I1–I6) | `/api/v1/ui/scoring` | Real endpoint exists; hardcoded fallback values present |
| Ring 5 gates | `/api/v1/ui/ring5` | Real endpoint exists; hardcoded fallback |
| Ω-Logos (I₆) sub-scores | `/api/v1/ui/omega_logos` | Real endpoint; hardcoded fallback |
| Autonomy tiers | `/api/v1/ui/autonomy` | Real endpoint; no hardcoded tiers |
| Engine room layers/SSE | `/api/v1/engine/live` + SSE | Real; SSE connected |
| Alexandria receipts | `/api/v1/memory/receipts` | Real; reads JSONL chain from disk |
| System timeline | `/api/v1/system/timeline` | Real; reads receipt JSON files |
| Ring status (Mac app) | `RingStatus.canonical` | **Hardcoded static seeds — not live-polled** |
| Service health (Mac) | HealthPoller probing | Real polling |
| I7 Certification Power | **NO UI SURFACE** | Absent |
| I8 Self-Modification | **NO UI SURFACE** | Absent |
| PAP Ω shadow status | **NO UI SURFACE** | Absent |
| Aletheia-Control Ω / C25 | **NO UI SURFACE** | Absent |
| PRISM-Ω | **NO UI SURFACE** | Absent |
| ARMS scoring | **NO UI SURFACE** | Absent |
| Math calc kernel | **NO UI SURFACE** | Absent |
| Noetic / gnoseogenesis | **NO UI SURFACE** | Absent |
| DWM | **NO UI SURFACE, NO CODE** | Architecture-defined, implementation-pending |
| RIS (Reality Ingestion) | **NO UI SURFACE** | Absent |
| Model Router | **NO UI SURFACE** | Absent |
| Contradiction graph | **NO UI SURFACE** | Absent |
| Corpus ingestion status | **NO UI SURFACE** | Absent |
| Proof carriers (CPS) | **NO UI SURFACE** | Absent |
| Reversibility registry | **NO UI SURFACE** | Absent |
| Goal formation | **NO UI SURFACE** | Absent |
| Drift monitor | **NO UI SURFACE** | Absent |
| Efficiency ledger | **NO UI SURFACE** | Absent |
| Symphony OS | **NO UI SURFACE** | Absent |
| Product portfolio | **NO UI SURFACE** | Absent |

---

## 5. Auth / Access Model

- No JWT or session auth in current UI.
- YubiKey slot 1 enrolled (`26116460`). Slot 2 pending (Ring 5 gate G4).
- No role-based access control in UI layer — single founder principal assumed.
- ns_api exposes `*` CORS — intentional for local sovereign deployment; not production-external.

---

## 6. Test Coverage

| Layer | Count | Status |
|-------|-------|--------|
| pytest (services) | 1,760 collected | 0 failed |
| vitest (ns_ui) | 21 | passing |
| XCTest (Mac bridge) | 9 | passing |
| Playwright / e2e | **ABSENT** | Not configured |
| Contract tests | ns_ui/__tests__/ | Partial (data contract tests present) |
| Route existence tests | **ABSENT** | Not configured |
| Component render tests | **ABSENT** | Not configured |

---

## 7. Build Commands

```bash
# ns_ui (canonical)
cd ns_ui && npm run dev          # :3001
cd ns_ui && npm run build
cd ns_ui && npm run test         # vitest run

# frontend (legacy)
cd frontend && npm run dev       # :3000
cd frontend && npm run build

# Mac app
./build_ns_mac.sh                # xcodebuild → apps/NS Infinity.app
# Or via SPM:
cd apps/ns_mac && swift test

# ns_api (backend)
# Started via docker-compose.yml or NS_BOOT.sh
```

---

## 8. Known Broken / Incomplete Paths

1. **`/autonomy` tiers array** — endpoint returns `tiers: []` with no fallback; page renders "Tier 0" grid with no data.
2. **`/[slug]` catch-all** — dynamic slug routes are wired but not yet populated with subsystem pages.
3. **Mac app Ring status** — `RingStatus.canonical` is static seed data; health poller does not write back to ring status.
4. **`apps/ns-tauri/`** — skeleton only; no UI content.
5. **Engine Room SSE** — `subscribeEngineLive` silently falls back to polling if SSE unavailable; no explicit SSE health indicator in UI.
6. **Scoring page I7/I8** — hardcoded fallback table only includes I1–I6; I7 (99.9 certification power) and I8 (self-modification) are absent.
7. **`frontend/`** — dist built but no longer the canonical UI; orphaned.
8. **PAP Ω** — shadow mode active, graduation scheduled 2026-05-04, zero UI surface.
9. **`docs/ui/`** — did not exist prior to this report (created now).
