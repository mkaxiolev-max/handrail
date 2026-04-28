# NS∞ UI — Implementation Backlog

**Version:** 1.0 · 2026-04-27  
**Branch:** `integration/xctest-20260427`  
**Ordered by priority (P1 = highest). Do not start P2 items until P1 is complete.**

---

## P1 — Critical / Graduation-Blocking

### P1.1 — PAP Ω Console (`/pap`)

**Why:** Graduation review scheduled 2026-05-04. Zero UI. Cannot observe PAP shadow metrics.  
**Gap matrix severity:** CRITICAL  
**Score impact:** 3.0 points  

Steps:
1. Verify `/api/v1/pap/status` endpoint exists in `services/pap/api/pap_routes.py`
2. If absent, add GET `/api/v1/pap/status` returning `PAPStatusResponse`
3. Create `ns_ui/src/app/pap/page.tsx`
4. Create widgets: `PAPPanel`, `PAPShadowStatus`, `PAPTriadicFloor`, `PAPGraduationCountdown`
5. Add `DWMStatusPill` equivalent for PAP in Founder Home
6. Add `pap` nav item to `FounderSidebar`
7. Add `pap` to `SECTIONS` manifest
8. Write 4 vitest contract tests
9. Write 2 pytest integration tests
10. Add `HabitatMode.pap` to Mac app

---

### P1.2 — I7 + I8 in Scoring Page

**Why:** I7 = 99.9 certification power and I8 = 136+ tests live but zero UI surface.  
**Gap matrix severity:** CRITICAL  
**Score impact:** I7: 3.5 pts, I8: 3.0 pts  

Steps:
1. Add I7 and I8 rows to scoring page fallback table
2. Extend `/api/v1/ui/scoring` to include I7 and I8 in instruments array
3. Add I7 badge to Founder Home (`I7CertificationPower = 99.9`)
4. Add I8 status pill to Organism Overview
5. Write vitest tests: `unit:I7-present`, `unit:I8-present`
6. Write pytest tests: `test_I7_score_is_present`, `test_I8_score_is_present`

---

### P1.3 — DWM Service + Console (`/dwm`)

**Why:** DWM is being integrated into NS. No code exists. First step is service skeleton.  
**Gap matrix severity:** CRITICAL  
**Score impact:** 4.0 points  

Steps (see `NS_UI_DWM_INTEGRATION_SPEC.md` for full sequence):
1. Create `services/dwm/` skeleton
2. Create `abi/schemas/DWMAction.v1.json` + `DWMReceipt.v1.json`
3. Add `/api/v1/dwm/status` endpoint returning `{ integration_state: "not_implemented" }`
4. Create `ns_ui/src/app/dwm/page.tsx` with `DWMConsole`
5. Add `DWMStatusPill` (grey, "architecture-defined") to Founder Home
6. Add `dwm` nav item to `FounderSidebar`
7. Wire Aletheion + Handrail bridges when DWM is ready for shadow mode
8. Write 8 required tests (see DWM spec)

---

### P1.4 — EpistemicBadge Primitive

**Why:** Core design principle: every claim must show its epistemic class. Currently zero enforcement in UI.  
**Gap matrix severity:** CRITICAL (cross-cutting)  

Steps:
1. Create `ns_ui/src/components/ui/EpistemicBadge.tsx`
2. Support 7 classes: `OBSERVED_FACT | REPORTED_CLAIM | DERIVED_INFERENCE | PROMOTED_CANON | SPECULATION | BLOCKED_ACTION | PENDING_REVIEW`
3. Each class has: color, icon, aria-label
4. Apply to: Engine Room live events, Alexandria atoms, receipt display, DWM actions
5. Write vitest tests: all 7 classes render

---

## P2 — High Priority / Score-Critical

### P2.1 — Score Reconciler v3.1/v3.2/v3.3 Panel

**Why:** Authoritative score is 97.42 v3.1 but UI only shows v2.1 / v3.0.  
**Score impact:** 2.0 points  

Steps:
1. Add v3_1 field to `/api/v1/ui/scoring` response
2. Update scoring page to show v3.1 as primary score
3. Add `TheoreticalCeilingPanel` — max achievable with Ring 5 open
4. Add `DeltasTo99` component — per-instrument delta to reach 99

---

### P2.2 — Aletheia-Control Ω Console (`/aletheia`)

**Why:** C25 golden corpus + Ω-Control tested but zero UI.  
**Score impact:** 2.5 points  

Steps:
1. Verify `/api/v1/aletheia_control/status` exists
2. Create `ns_ui/src/app/aletheia/page.tsx`
3. Widgets: `AletheiaControlPanel`, `C25ScorePanel`, `GoldenCorpusStatus`, `WisdomCourageAcceptance`, `ConcernWasteRoute`
4. Add `aletheia` nav item
5. Write 3 vitest contract tests + 2 pytest integration tests

---

### P2.3 — Logos Gate Risk Scores (in Governance)

**Why:** Logos Gate status shown as single score but deception/coercion/domination triad absent.  
**Score impact:** 1.5 points  

Steps:
1. Add `LogosGatePanel` with risk score triad to governance page
2. Wire to `/api/v1/aletheion/logos/status`
3. Add `ConstitutionalWarning` overlay when status = BLOCK
4. Write vitest test: BLOCK triggers warning

---

### P2.4 — PRISM-Ω Console (`/prism`)

**Why:** PRISM-Ω is the multi-axis synthesis engine. Zero UI.  
**Score impact:** 3.0 points  

Steps:
1. Verify `services/prism_omega` API routes
2. Add `/api/v1/prism/status` to ns_api if absent
3. Create `ns_ui/src/app/prism/page.tsx`
4. Widgets: `PRISMOmegaPanel`, `PRISMAxisBreakdown`, `PRISMSynthesisLog`

---

### P2.5 — Noetic / Intent Kernel Console (`/noetic`)

**Why:** Noetic is core to gnoseogenesis. Zero UI.  
**Score impact:** 2.5 points  

Steps:
1. Verify `services/noetic` API routes
2. Create `ns_ui/src/app/noetic/page.tsx`
3. Widgets: `NoeticPanel`, `IntentKernelMonitor`, `GnoseogenesisLog`

---

### P2.6 — ReceiptDrawer (universal)

**Why:** Every SHA-256 displayed should open a receipt drawer. Currently none exist.  
**Cross-cutting — required by all surfaces.**  

Steps:
1. Create `ns_ui/src/components/shell/ReceiptDrawer.tsx`
2. Wire to Zustand store: `{ openReceiptId: string|null, setOpenReceiptId }`
3. Apply to: scoring, memory, governance, engine room, PAP, Aletheia, DWM

---

### P2.7 — Ring Status Live Poll

**Why:** Ring status in Mac app is static seed data. ns_ui home shows no ring grid.  
**Score impact:** 2.0 points  

Steps:
1. Add `/api/v1/ui/rings` endpoint returning 7 ring objects
2. Create `RingStatusGrid` component for ns_ui
3. Update Mac app `HealthPoller` to write ring status from API
4. Add ring grid to Founder Home and Organism page

---

### P2.8 — Handrail CPS Panel (extended)

**Why:** Engine Room shows adjudication but no proof carriers, reversibility, CPS packet detail.  
**Score impact:** 2.0 points  

Steps:
1. Extend `/api/v1/engine/live` response to include `proof_carriers` and `reversibility`
2. Add `HandrailCPSPanel` + `ProofCarrierList` to Engine Room page
3. Add `ReversibilityRegistryPanel` to Engine Room

---

## P3 — Medium Priority

### P3.1 — Drift Monitor (`/drift`)
Create drift monitor page. Wire `services/drift_monitor`. Add `DriftTimeline` Recharts component.

### P3.2 — Aletheion v2 Gate Matrix (in Governance)
Add `AletheionGateMatrix` showing logos / canon_readiness / pre_action gate states.

### P3.3 — RIS Console (`/ris`)
Create reality ingestion console. Wire `services/reality_ingest`. Add source grid + ingestion receipts.

### P3.4 — Model Router Console (`/models`)
Create sovereign compute console. Read from `ns_local_brain_manifest.json` + model_router service.

### P3.5 — ARMS Scoring (`/arms`)
Create ARMS scoring page. Wire `services/arms_scoring`.

### P3.6 — Dignity Kernel + HIC Panel
Add `DignityKernelPanel` + `HICPatternList` to Governance page.

### P3.7 — Canon Promotion Queue
Add `CanonPromotionQueue` with six-fold gate progress to Governance page.

### P3.8 — IrreversibleActionConfirm Flow
Create 3-step confirmation component. Apply to any action tagged `IRREVERSIBLE`.

### P3.9 — ContradictionGraph
Add ReactFlow graph of conflicting evidence pairs to Alexandria page.

### P3.10 — NCOM Readiness Panel + Collapse Modal
Add `NCOMReadinessPanel` to Governance. Add `CollapseReadyModal` triggered by threshold.

---

## P4 — Normal Priority

### P4.1 — Corpus Ingestion Status
Add ingestion job status to Alexandria page.

### P4.2 — Goal Formation Panel
Add `GoalFormationPanel` to Engine Room.

### P4.3 — Continuum / ROOT Panel
Add Continuum state detail to Engine Room or dedicated route.

### P4.4 — Command Palette (⌘K)
Operator command palette — search routes, actions, subsystem status.

### P4.5 — Sentinel + Canon Promotion Queue
Add `SentinelWatchList` to Governance.

---

## P5 — Mac App Parity

1. Add `HabitatMode.pap`, `.dwm`, `.aletheia`, `.ris`, `.models` cases
2. Update `LeftRail` icons for new modes
3. Create PAP, DWM, Aletheia feature views (SwiftUI)
4. Update `HealthPoller` to write live ring status to AppState
5. Add I7 + I8 to `OmegaView`

---

## P6 — Test Coverage

1. Configure Playwright: `cd ns_ui && npx playwright install`
2. Write 10 route existence tests
3. Write 5 component render tests
4. Write 5 accessibility tests
5. Write No-Mocked-Data integration tests

---

## P7-P9 — Product Portfolio, Symphony OS, External Products

**Defer until Ring 5 gates cleared (Stripe DNS + YubiKey slot 2).**

---

## Completion Criteria for 95+ UI Score

- [ ] P1.1 PAP Console live
- [ ] P1.2 I7 + I8 in Scoring
- [ ] P1.3 DWM service skeleton + `/dwm` console (shows not_implemented)
- [ ] P1.4 EpistemicBadge applied to all data surfaces
- [ ] P2.1 Score Reconciler v3.1
- [ ] P2.2 Aletheia-Control Console
- [ ] P2.6 ReceiptDrawer universal
- [ ] P2.7 Ring Status live poll
- [ ] P2.8 Handrail CPS extended
- [ ] All vitest tests pass (target: 60+)
- [ ] All pytest UI contract tests pass
