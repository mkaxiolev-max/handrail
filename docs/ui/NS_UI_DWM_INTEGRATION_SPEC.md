# NS∞ DWM Integration Specification

**Version:** 1.0 · 2026-04-27  
**Branch:** `integration/xctest-20260427`  
**Status:** Architecture-defined — implementation-pending  
**Code found in repo:** NONE  
**DWM canonical name:** Daily Work Monitor / Dynamic Work Management (to be confirmed against NS documentation)

---

## 1. Current State

DWM is referenced in the canonical NS∞ architecture state as "now being integrated into NS." As of 2026-04-27:

- No `services/dwm/` directory exists
- No DWM API routes found in any Python service
- No DWM UI surface exists in ns_ui or ns_mac
- No DWM tests exist
- No DWM schemas exist in `abi/schemas/`
- No DWM entries exist in `API_REFERENCE.json`

This document defines the integration architecture DWM must conform to when implemented.

---

## 2. DWM Conceptual Role in NS∞

DWM is a first-class NS integration layer that bridges the operator's daily workflow into the constitutional organism. Its role is to:

1. Receive structured work items from the operator or external systems
2. Route work items through NS constitutional gates before execution
3. Generate proof-carrying receipts for all work actions
4. Report DWM-sourced evidence back into Alexandria
5. Contribute to the score via new I-series or sub-score dimensions
6. Respect autonomy tier ceiling — no DWM action may exceed Tier 3 without escalation
7. Surface DWM state, gaps, and impact in the operator UI

---

## 3. DWM Ring Integration Map

| Ring | DWM Interaction | Enforcement Point |
|------|----------------|-------------------|
| Ring 1 | DWM receives constitutional invariant constraints | Aletheion v2 pre-action gate |
| Ring 2 | DWM action payloads authenticated through Logos Gate | Logos Gate risk score check |
| Ring 3 | DWM execution proof-carried through Handrail CPS | CPS packet generation per DWM action |
| Ring 4 | DWM outputs entered into Alexandria receipt ledger | SHA-256 receipt chain append |
| Ring 5 | DWM graduation subject to Ring 5 external gate clearance | Manual gate G4/G5 dependency |
| Ring 6 | DWM scope bounded by autonomy tier ceiling (Tier ≤ 3) | Tier check before dispatch |
| Ring 7 | DWM wisdom outputs may contribute to Storytime | Storytime ingestion hook |

---

## 4. DWM Instrument Integration

DWM integration is expected to contribute to the following instruments:

| Instrument | DWM Contribution |
|-----------|-----------------|
| I3 (UOIE v2) | DWM provides unified operator-intent evidence |
| I4 (GPX-Ω) | DWM actions feed GPX-Ω goal-pursuit evidence |
| I7 (Certification Power) | DWM certification workflows contribute to I7 |

DWM may also justify a new instrument (e.g., I9 — Operational Integration) pending architecture review.

---

## 5. Required Service Implementation

### 5.1 Service skeleton: `services/dwm/`

```
services/dwm/
├── __init__.py
├── Dockerfile
├── main.py              # FastAPI app
├── models.py            # DWMAction, DWMReceipt, DWMState
├── router.py            # API routes
├── handrail_bridge.py   # CPS packet dispatch
├── aletheion_bridge.py  # Pre-action gate
├── canon_bridge.py      # Alexandria receipt append
├── receipts.py          # Receipt generation
└── tests/
    ├── test_dwm_models.py
    ├── test_dwm_receipts.py
    └── test_dwm_handrail_bridge.py
```

### 5.2 Required API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/dwm/status` | Current DWM integration state |
| POST | `/api/v1/dwm/actions` | Submit work action through constitutional gates |
| GET | `/api/v1/dwm/actions` | List recent DWM actions |
| GET | `/api/v1/dwm/receipts` | List DWM receipts |
| GET | `/api/v1/dwm/receipts/{id}` | Get specific receipt |
| GET | `/api/v1/dwm/gaps` | List integration gaps |
| GET | `/api/v1/dwm/score_impact` | Score impact of DWM integration |

### 5.3 DWM Action Flow

```
Operator submits DWM action
        │
        ▼
Aletheion v2 pre_action gate
    │          │
 PASS        BLOCK → receipt(blocked), return BLOCK to UI
    │
    ▼
Logos Gate risk score check
    │          │
 PASS        WARN → receipt(warn), continue with warning
    │
    ▼
Autonomy tier check (≤ Tier 3?)
    │          │
  YES          NO → escalation required
    │
    ▼
Handrail CPS packet dispatch
    │
    ▼
Execute action (with reversibility tag)
    │
    ▼
SHA-256 receipt → Alexandria chain
    │
    ▼
DWM log entry + score_impact update
```

---

## 6. DWM Schema (ABI)

Schema file to be created: `abi/schemas/DWMAction.v1.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema",
  "title": "DWMAction",
  "version": "1",
  "properties": {
    "action_id": { "type": "string", "format": "uuid" },
    "operator_intent": { "type": "string" },
    "action_type": { "type": "string" },
    "payload": { "type": "object" },
    "reversible": { "type": "boolean" },
    "autonomy_tier_required": { "type": "integer", "minimum": 0, "maximum": 5 },
    "submitted_at": { "type": "string", "format": "date-time" }
  },
  "required": ["action_id", "operator_intent", "action_type", "payload", "reversible"]
}
```

Schema file to be created: `abi/schemas/DWMReceipt.v1.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema",
  "title": "DWMReceipt",
  "version": "1",
  "properties": {
    "receipt_id": { "type": "string" },
    "sha256": { "type": "string" },
    "action_id": { "type": "string" },
    "gate_results": {
      "type": "object",
      "properties": {
        "aletheion": { "type": "string", "enum": ["PASS", "WARN", "BLOCK"] },
        "logos": { "type": "string", "enum": ["PASS", "WARN", "BLOCK"] },
        "autonomy_tier": { "type": "string", "enum": ["PASS", "ESCALATE"] }
      }
    },
    "outcome": { "type": "string", "enum": ["EXECUTED", "BLOCKED", "ESCALATED"] },
    "cps_packet_id": { "type": "string" },
    "timestamp": { "type": "string", "format": "date-time" },
    "parent_sha256": { "type": "string" }
  },
  "required": ["receipt_id", "sha256", "action_id", "gate_results", "outcome", "timestamp"]
}
```

---

## 7. DWM UI Requirements

### 7.1 DWM Console (`/dwm` route)

**Required widgets:**

| Widget | Description |
|--------|-------------|
| `DWMStatePanel` | Integration state: `not_implemented \| initializing \| active \| degraded` |
| `DWMInputOutputLog` | Scrollable log of inputs received and outputs generated |
| `DWMReceiptList` | Recent receipts with SHA-256 links to ReceiptDrawer |
| `DWMIntegrationMap` | Visual map (ReactFlow or SVG) of which Rings DWM integrates |
| `DWMScoreImpact` | Number: score points contributed by DWM integration |
| `DWMGapList` | Ordered list of unresolved DWM implementation gaps |
| `DWMTestStatus` | Test coverage indicator for DWM service |

**Epistemic rule:** DWM action outcomes must display their epistemic class:
- EXECUTED → `OBSERVED_FACT`
- BLOCKED → `BLOCKED_ACTION`
- ESCALATED → `PENDING_REVIEW`

### 7.2 DWM in Founder Home

The Founder Home must include a `DWMStatusPill`:
- When `not_implemented`: grey pill, label "DWM: architecture-defined"
- When `active`: green pill, label "DWM: active"
- When `degraded`: amber pill, label "DWM: degraded"

### 7.3 Mac App DWM Mode

Add `HabitatMode.dwm = "DWM Console"` to `AppState.swift` with icon `cpu.fill`.

---

## 8. DWM Tests Required

| Test | Type | File |
|------|------|------|
| DWM action model valid | unit | `services/dwm/tests/test_dwm_models.py` |
| DWM receipt chain | unit | `services/dwm/tests/test_dwm_receipts.py` |
| Handrail bridge dispatches CPS | integration | `services/dwm/tests/test_dwm_handrail_bridge.py` |
| Aletheion pre-action gate blocks | integration | `tests/dwm/test_dwm_aletheion.py` |
| Logos gate BLOCK stops execution | integration | `tests/dwm/test_dwm_logos.py` |
| Autonomy tier ceiling enforced | unit | `tests/dwm/test_dwm_autonomy.py` |
| DWM UI state displays absent correctly | vitest | `ns_ui/__tests__/dwm.test.ts` |
| DWM receipt links to Alexandria | integration | `tests/dwm/test_dwm_receipt_chain.py` |

---

## 9. Implementation Sequence

1. Write `abi/schemas/DWMAction.v1.json` and `abi/schemas/DWMReceipt.v1.json`
2. Create `services/dwm/` skeleton (models, receipts)
3. Wire Aletheion bridge (copy pattern from `services/pap/aletheion_bridge.py`)
4. Wire Handrail bridge (copy pattern from `services/pap/handrail_bridge.py`)
5. Implement `/api/v1/dwm/status` endpoint (returns `not_implemented` until step 6)
6. Add `dwm` router to `services/ns_api/app/main.py`
7. Create `ns_ui/src/app/dwm/page.tsx` with DWMConsole
8. Add `DWMStatusPill` to Founder Home
9. Add `HabitatMode.dwm` to Mac app
10. Write all 8 required tests
11. Confirm score_impact calculation
12. Graduate DWM from `not_implemented` → `active` after tests pass
