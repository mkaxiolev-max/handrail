# NS∞ UI — Target Architecture

**Version:** 1.0 · 2026-04-27  
**Applies to:** `integration/xctest-20260427` → forward  
**Design principle:** Every claim displayed must visibly carry its epistemic class.  
**Never collapse** evidence, inference, and Canon into one undifferentiated surface.

---

## 1. Epistemic Display Rule

Every data point shown in the UI MUST visibly carry one of these seven classes:

| Class | Badge | Color |
|-------|-------|-------|
| `OBSERVED_FACT` | ● observed | `#00FF88` |
| `REPORTED_CLAIM` | ◈ reported | `#88CCFF` |
| `DERIVED_INFERENCE` | ◇ inferred | `#FFAA00` |
| `PROMOTED_CANON` | ★ canon | `#FFD700` |
| `SPECULATION` | ○ speculative | `#888888` |
| `BLOCKED_ACTION` | ✕ blocked | `#FF3333` |
| `PENDING_REVIEW` | ◉ pending | `#AA44FF` |

---

## 2. Navigation Model

### Primary surfaces (11 → 22 target)

```
Sidebar (left, 164px fixed)
├── Founder Home          [home]         ● organism overview
├── Living Architecture   [living]       ● ring/instrument map
├── Engine Room           [engine]       ● handrail CPS + execution
├── Governance + Canon    [governance]   ● dignity/logos/sentinel/PAP
├── Memory / Alexandria   [alexandria]   ● atoms/canon/receipts
├── Truth / Aletheia      [aletheia]     [NEW] C25/Ω-Control
├── DWM Console           [dwm]          [NEW] DWM integration
├── Scoring / Omega       [scoring]      ● instruments + deltas
├── Ω-Logos (I₆)          [omega_logos]  ● I₆ deep
├── RIS Console           [ris]          [NEW] reality ingestion
├── Model Router          [models]       [NEW] sovereign compute
├── PAP Console           [pap]          [NEW] PAP shadow/graduation
├── PRISM-Ω               [prism]        [NEW] multi-axis synthesis
├── ARMS Scoring          [arms]         [NEW] arms detail
├── Noetic / Intent       [noetic]       [NEW] gnoseogenesis
├── Drift Monitor         [drift]        [NEW] drift + efficiency
├── Continuum / ROOT      [continuum]    [NEW] continuum state
├── Product Portfolio     [portfolio]    [NEW] launch gates
├── Ring 5 Gates          [ring5]        ● external gates
├── Autonomy Tiers        [autonomy]     ● tier ceiling
├── Voice / Violet        [voice]        ● violet state
└── Build + Receipts      [build]        ● receipts ledger
```

### Secondary surfaces (modal / drawer)

- **Receipt Drawer** — slides from right on any receipt SHA-256 click
- **Audit Drawer** — shows full proof chain for any action
- **Operator Command Palette** — ⌘K trigger, searchable actions with confirmation flows
- **Collapse-Ready Modal** — full-screen alert when NCOM/collapse threshold triggered
- **Irreversible Action Confirmation** — 3-step confirm for any action tagged `IRREVERSIBLE`
- **Constitutional Warning Flow** — triggered when Logos Gate status = BLOCK

---

## 3. Surface Specifications

### 3.1 Founder Home (Organism Overview)

**Purpose:** Global health at a glance. No raw data — synthesized truth only.

**Widgets:**
- `GlobalShalom` — boolean ring: is organism in Shalom state?
- `MasterScore` — v3.1 live score (from scoring service)
- `RingStatusGrid` — 7 rings, each showing: OK / WARN / BLOCK
- `InstrumentStatusGrid` — I1–I8, each with score + status
- `PendingGates` — Ring 5 open items + PAP graduation + active external blockers
- `CanonicalHEAD` — current git commit + branch
- `ActiveWarnings` — sorted by severity

**New widgets needed:**
- `I7CertificationPower` — live I7 = 99.9
- `I8SelfModStatus` — I8 shadow status
- `PAPGraduationCountdown` — days to 2026-05-04 graduation review
- `DWMStatusPill` — DWM integration signal (absent → architecture-defined)

---

### 3.2 Engine Room

**Purpose:** Execution surface — what is happening, what ran, what failed.

**Widgets:**
- `HandrailCPSPanel` — moat status, queue depth, last op
- `ActionQueue` — pending CPS packets with proof carrier status
- `ProofCarrierList` — each execution unit's proof chain
- `ReversibilityRegistry` — reversible vs irreversible action counts + registry link
- `ExecutionReceipts` — last N receipts with SHA-256 links
- `MacPlaneStatus` — Mac adapter / adapters/mac health
- `FailureEscalation` — failures with context + escalation path
- `SSEStatusPill` — live vs polling indicator (currently exists)

**New widgets needed:**
- `GoalFormationPanel` — active goals, formation method
- `ActionOutcomeLoop` — outcome vs expectation comparison
- `EfficiencyLedger` — efficiency scores per action class

---

### 3.3 Governance + Canon

**Purpose:** Constitutional status — what is law, what is at risk.

**Widgets:**
- `DignityKernelStatus` — Hamiltonian gate state
- `LogosGatePanel` — deception/coercion/domination risk scores
- `AletheionStatus` — v2 gate states (logos, canon readiness, pre-action)
- `SentinelPanel` — active sentinel watches
- `CanonPromotionQueue` — pending promotions, six-fold gate progress
- `ConstitutionalAmendments` — amendment log + pending
- `PAPPanel` — shadow mode status, triadic floor status, graduation readiness
- `AletheiaControlPanel` — Ω / C25 score, golden corpus status (see 3.5)
- `HICPatterns` — live count, recent triggers
- `NCOMReadiness` — collapse readiness indicator

---

### 3.4 Memory / Alexandria

**Purpose:** Evidence store — every claim traceable to origin.

**Epistemic requirement:** MUST visibly distinguish atoms / molecules / canon / compressed wisdom.

**Widgets:**
- `EvidenceAtomBrowser` — filterable by source, type, timestamp
- `StructuredMolecules` — atom clusters with provenance chains
- `CanonLedger` — promoted canon entries with promotion receipt SHA-256
- `CompressedWisdom` — Storytime entries
- `ProvenanceChain` — visual chain from observation → inference → canon
- `ContradictionGraph` — ReactFlow graph of conflicting evidence pairs
- `CorpusIngestionStatus` — in-progress / completed corpus ingestion jobs
- `AlexandriaChainHealth` — receipt chain validity indicator

---

### 3.5 Truth / Aletheia Console

**Purpose:** Aletheia-Control Ω and C25 — the golden corpus and wisdom/courage/acceptance triad.

**Widgets:**
- `AletheiaControlOmega` — current Ω-Control score
- `C25ScorePanel` — C25 composite (25 golden corpus questions status)
- `GoldenCorpusStatus` — which C25 questions are resolved vs open
- `ConcernWasteRoute` — ConcernWasteRoute classifier output
- `ControlInfluenceConcernMixed` — 4-bucket classifier live distribution
- `WisdomCourageAcceptance` — triadic floor scores
- `EpistemicClassDistribution` — how evidence is classified across the corpus

---

### 3.6 DWM Console

**Architecture-defined — implementation pending as of 2026-04-27.**

DWM (Daily Work Monitor / Dynamic Work Management — exact canonical naming to be confirmed from NS documentation once code is written) is being integrated into NS as a first-class Ring integration.

**Target widgets:**
- `DWMStatePanel` — DWM current integration state
- `DWMInputOutputLog` — what DWM receives from NS and returns
- `DWMReceiptList` — receipts generated from DWM operations
- `DWMIntegrationMap` — which Rings and Instruments DWM touches
- `DWMScoreImpact` — how DWM integration affects v3.x score
- `DWMGapList` — what DWM needs from NS that doesn't exist yet
- `DWMTestStatus` — test coverage for DWM integration layer

**DWM Ring integration map (target):**

| Ring | DWM Role |
|------|----------|
| Ring 1 | DWM receives constitutional constraints |
| Ring 2 | DWM execution authenticated through Logos Gate |
| Ring 3 | DWM actions proof-carried through Handrail CPS |
| Ring 4 | DWM outputs entered into Alexandria receipt ledger |
| Ring 5 | DWM graduation subject to external gate clearance |
| Ring 6 | DWM scope bounded by autonomy tier ceiling |
| Ring 7 | DWM wisdom outputs may contribute to Storytime |

---

### 3.7 Scoring / Omega Dashboard

**Purpose:** Score truth — current, ceiling, deltas.

**Widgets:**
- `MasterScoreV31` — current 97.42
- `MasterScoreV32` — projected (pending I7/I8 full integration)
- `MasterScoreV33` — projected (pending PAP graduation)
- `InstrumentBreakdown` — I1–I8 scores, weights, weighted contribution
- `TheoreticalCeiling` — maximum achievable with Ring 5 open
- `DeltasTo99` — what's needed per instrument to reach 99+
- `ScoreTimeline` — drift/growth graph (Recharts sparkline)
- `ScoreImpactOfMissingUI` — score points locked by absent UI surfaces
- `SubsystemScores` — per-service scoring contributions

---

### 3.8 RIS Console (Reality Ingestion)

**Purpose:** What's flowing in from the real world.

**Widgets:**
- `SourceGrid` — USPTO, SEC, news, technical/research, regulatory, standards
- `SourceCredibility` — credibility score per source type
- `EvidenceTypingLog` — recent evidence typed by RIS
- `IngestionReceipts` — hash-linked ingestion events
- `IngestQueueDepth` — pending ingestion jobs
- `IngestionHealth` — service health for reality_ingest service

---

### 3.9 Model Router / Sovereign Compute

**Purpose:** What intelligence is running and at what cost.

**Widgets:**
- `LocalModelRegistry` — local models from `ns_local_brain_manifest.json`
- `CloudModelStatus` — cloud model routing status
- `RoutingPolicy` — current routing rules
- `PrivacyBudget` — what data flows to cloud vs stays local
- `ContextBudget` — token budget utilization
- `ModelEvalScores` — per-model eval results
- `CostLatencyMatrix` — cost/latency per model

---

### 3.10 Product Portfolio

**Purpose:** Launch gates for NS products.

**Widgets per product:** NS∞, Handrail, ROOT, Symphony OS, Pain-Resolution Stack, Wearable Power

Per product:
- `ProductStatusPill` — pre-launch / beta / live
- `LaunchGateChecklist` — technical + legal + business gates
- `ExternalGateLinks` — DNS / Stripe / legal dependencies

---

## 4. Layout Hierarchy

```
Root Layout
├── Sidebar (164px, fixed, dark #080C1E)
│   ├── Brand mark (NS∞ + AXIOLEV)
│   ├── NavItems (11 → 22)
│   └── ServiceStatusMini (bottom)
├── TopBar (48px, fixed)
│   ├── CurrentMode label
│   ├── GlobalShalom indicator
│   ├── MasterScore pill
│   └── CanonicalHEAD (git SHA)
├── MainContent (flex-1, scrollable)
│   └── [Page content]
└── StatusStrip (24px, fixed bottom)
    ├── SSE connection status
    ├── Last receipt timestamp
    └── Active warnings count
```

---

## 5. Design System

### 5.1 Color System

**Semantic colors:**

| Token | Hex | Use |
|-------|-----|-----|
| `founder` | `#FF6B00` | Founder-level actions |
| `violet` | `#00D4FF` | Violet/voice/identity |
| `adjudication` | `#00FF88` | Adjudication, healthy |
| `handrail` | `#00FFFF` | Handrail / CPS |
| `alexandria` | `#FFFF00` | Memory / receipts |
| `kernel` | `#FF3333` | Critical / blocked |
| `warning` | `#FFAA00` | Warning state |
| `canon` | `#FFD700` | Promoted canon |
| `governance` | `#AA44FF` | Constitutional / governance |
| `ris` | `#44AAFF` | Reality ingestion |
| `dwm` | `#FF88AA` | DWM integration |
| `bg` | `#0A0E27` | Background |
| `surface` | `#080C1E` | Sidebar / elevated surface |
| `border` | `#1E3A5F` | Default border |

### 5.2 Status Indicators

| State | Color | Shape |
|-------|-------|-------|
| PASS / HEALTHY | `#00FF88` | ● filled circle |
| WARN | `#FFAA00` | ◆ diamond |
| BLOCK / CRITICAL | `#FF3333` | ✕ |
| PENDING | `#AA44FF` | ◉ ring |
| ABSENT / UNIMPLEMENTED | `#444466` | ○ hollow |
| SHADOW MODE | `#FFAA44` | ◈ half-filled |

### 5.3 Card Pattern

```
┌────────────────────────────────────────┐
│ [10px] SUBSYSTEM NAME   [status pill]  │
├────────────────────────────────────────┤
│                                        │
│  Content / metrics                     │
│                                        │
│ [receipt link]    [last updated]       │
└────────────────────────────────────────┘
```

### 5.4 Receipt Drawer

Slides in from right (320px). Shows:
1. Receipt SHA-256 (copyable)
2. Receipt type
3. Timestamp
4. Parent receipt link (provenance chain)
5. Full JSON payload (collapsible)

### 5.5 Operator Command Palette (⌘K)

- Searches actions, routes, subsystem status
- Actions requiring confirmation show confirmation step before execution
- Irreversible actions require 3-step confirm: intent → review → confirm
- Constitutional warnings show before any action that touches Logos Gate

### 5.6 Collapse-Ready Modal

Full-screen overlay triggered when NCOM collapse readiness threshold is crossed:
1. Collapse state summary
2. Active constitutional constraints
3. Action checklist
4. One-click escalation to founder

---

## 6. State Management

| Layer | Technology | Scope |
|-------|-----------|-------|
| Server state | TanStack React Query v5 | API data, caching, refetch |
| UI state | Zustand v5 | navigation, drawer open/close, mode |
| SSE stream | Custom hook (`subscribeEngineLive`) | real-time engine events |
| Mac state | AppState ObservableObject | SwiftUI environment |

---

## 7. Mac App Target State

The Mac app (`NSInfinityApp`) should mirror the ns_ui route set, plus add:
- **Metal organ viz** — ring topology rendered via OrganismRenderer (partially exists)
- **Live ring status** — HealthPoller writes ring status from API
- **PAP mode** — HabitatMode case `.pap` for PAP console
- **DWM mode** — HabitatMode case `.dwm`
- **Aletheia mode** — HabitatMode case `.aletheia`
- **RIS mode** — HabitatMode case `.ris`
- **Scoring deep** — full I1–I8 breakdown in OmegaView
