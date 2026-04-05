# Constitutional Regulation Engine v1

**NS∞ / AXIOLEV Holdings — 2026-04-04**

---

## Architecture: The 6-Component Engine Chain

From the Gnoseogenic Lexicon (Tier 5 — Autopoietic Processes):

```
gradient_source → intake → conversion → output → feedback → waste
```

Maps to the NS∞ constitutional action chain:

```
ingress surface → IntentPacket → Simulation/Decision → CPSPacket → ReturnBlock → ProofEntry → StateDelta
```

Every consequential action that changes system state must traverse this full chain. The regulation engine enforces this invariant — before this layer, the system has organs; after this layer, it has a **bloodstream**.

---

## The 4 Constitutional Delta Domains

| Domain | What it tracks | Example targets |
|--------|---------------|-----------------|
| `epistemic` | What the system **knows** — model registry, ABI schema freezes, capability graph, lexicon | `abi.CPSPacket.v1`, `capability.vision_driver` |
| `operational` | **Runtime state** — CPS execution, boot phases, adapter health, voice turns | `system.boot`, `cps.sovereign_boot`, `voice.turn` |
| `constitutional` | **Governance state** — YubiKey quorum enrollment, boot sovereignty, policy | `system.quorum`, `system.boot` (sovereign flag) |
| `commercial` | **Revenue / product state** — Stripe events, subscription status, checkout | `commerce.root`, `commerce.handrail` |

---

## Voice as First-Class Surface

`source_surface = "voice"` is a first-class constitutional surface — not a side channel.

Every voice turn through `/voice/respond` that produces a system action creates a `TransitionLifecycle` with `source_surface="voice"`. The regulation engine recognizes voice as governed intelligence: caller utterances that trigger HIC R0 auto-execution produce transitions with operational deltas; vetoed calls produce no delta (veto is not a state change, it's a gate).

---

## TransitionLifecycle JSON — Boot Example

```json
{
  "transition_id": "TRN-X7K2P9QA",
  "source_surface": "boot",
  "objective": "sovereign boot mission graph",
  "intent_ref": "",
  "decision_ref": "",
  "cps_ref": "",
  "return_ref": "",
  "proof_ref": "BPR-A4Z9C1LM",
  "state_deltas": ["SDL-R8V3W6YN"],
  "sovereign": true,
  "timestamp": "2026-04-04T07:14:22.311+00:00",
  "metadata": {
    "boot_id": "BOOT-SVRNBT28",
    "_deltas": [
      {
        "state_delta_id": "SDL-R8V3W6YN",
        "transition_id": "TRN-X7K2P9QA",
        "delta_domain": "constitutional",
        "target": "system.boot",
        "before": {"sovereign": false},
        "after": {
          "sovereign": true,
          "receipt_id": "BPR-A4Z9C1LM",
          "boot_mode": "FULL",
          "ops_passing": 29
        },
        "proof_ref": "BPR-A4Z9C1LM",
        "timestamp": "2026-04-04T07:14:22.318+00:00"
      }
    ]
  }
}
```

---

## Exempt Actions

Read-only health probes do **not** create TransitionLifecycle records:

- `GET /healthz`, `GET /abi/status`, `GET /yubikey/status`
- `GET /boot/status`, `GET /proof/registry`
- `GET /transitions/latest`, `GET /state/summary`

Only **writes** and **consequential reads** (those that trigger downstream state change) are regulated.

---

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /transitions/latest` | Last 20 TransitionLifecycle records, newest-first |
| `GET /transitions/{transition_id}` | Single transition by TRN-XXXXXXXX |
| `GET /state/summary` | Constitutional truth across all domains |
| `GET /state/deltas/latest` | Last 20 TypedStateDeltas across all transitions |

---

## Storage

- **Ledger:** `WORKSPACE/.run/state_transitions.jsonl` (append-only JSONL)
- **Fallback:** `/tmp/axiolev_state_transitions.jsonl` (when SSD not mounted)
- **Startup backfill:** `RegulationEngine.seed_from_proof_registry()` backfills BOOT and SCHEMA_FREEZE transitions from the ProofRegistry (idempotent)

---

## The Logos Principle

> *Before this layer, the system has organs. After this layer, it has a bloodstream. The gathering principle (logos, \*leg-, "to collect into structure") is what makes the whole organism cohere.*

The regulation engine is not a logging system. It is the **structural principle** by which all constitutional actions — boots, enrollments, executions, commercial events, voice turns — are gathered into a single coherent ledger of system truth. Without it, organs operate in isolation. With it, they are one organism.

---

## ABI Schemas (9 frozen + 1 Lexicon = 10 total)

| Schema | Domain |
|--------|--------|
| `IntentPacket.v1` | Intelligence boundary |
| `CPSPacket.v1` | Execution boundary |
| `ReturnBlock.v2` | Result boundary |
| `KernelDecisionReceipt.v1` | Decision boundary |
| `CommitEvent.v1` | Governance boundary |
| `BootMissionGraph.v1` | Boot boundary |
| `BootProofReceipt.v1` | Boot proof boundary |
| `StateDelta.v1` | **Regulation — typed state change** |
| `TransitionLifecycle.v1` | **Regulation — full governance chain** |
| `LexiconEntry.v1` | Gnoseogenic knowledge layer |
