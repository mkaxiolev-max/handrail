# Constitutional Regulation Engine v1

**Date:** 2026-04-04 | **Status:** LIVE | **Tag:** `regulation-engine-v1`

---

## What it is

The Constitutional Regulation Engine is the unified governance loop — the bloodstream connecting all constitutional organs of NS∞. Every sovereign action now produces a `TransitionLifecycle` record that traces the full governance chain from intent to state change.

---

## Architecture

### TypedStateDelta — 4 constitutional domains

| Domain | What it tracks |
|--------|---------------|
| `epistemic` | Knowledge/memory state (model registry, capability graph) |
| `operational` | Runtime state (CPS execution, boot phases, adapter health) |
| `constitutional` | Governance state (YubiKey quorum, ABI freeze, policy) |
| `commercial` | Revenue/Stripe/subscription state |

### TransitionLifecycle — full governance chain

Every transition carries:
- `transition_id` (TRN-XXXXXXXX)
- `source_surface` (voice / text / console / api / system / boot)
- `objective` — human-readable intent
- `intent_ref` → `decision_ref` → `cps_ref` → `return_ref` → `proof_ref`
- `state_deltas[]` — ordered TypedStateDeltas
- `sovereign` boolean — true if YubiKey quorum was satisfied

### RegulationEngine — stateless class

```python
lc = RegulationEngine.begin("voice", "process voice command", metadata={...})
RegulationEngine.attach_cps(lc, cps_id)
RegulationEngine.append_delta(lc, "operational", "voice.turn", before, after)
RegulationEngine.finalize(lc)  # persists to .run/transitions.jsonl
```

---

## Storage

- **Transitions ledger:** `WORKSPACE/.run/transitions.jsonl` (append-only)
- **Startup seeding:** `RegulationEngine.seed_from_proof_registry()` backfills prior ProofRegistry entries idempotently
- **Factory module:** `services/handrail/handrail/regulation_engine.py`

---

## ABI Schemas (9 total — 2 new)

| Schema | Fingerprint |
|--------|-------------|
| `StateDelta.v1` | see `/abi/status` |
| `TransitionLifecycle.v1` | see `/abi/status` |

---

## Wired surfaces

| Surface | Where | What it records |
|---------|-------|-----------------|
| Boot | `/boot/proof` handler | operational boot delta + proof_ref |
| YubiKey enrollment | `/yubikey/enroll` handler | constitutional quorum delta |
| CPS execution | `/ops/cps` handler | operational CPS delta |
| Voice | NS `/voice/respond` handler | operational voice turn delta |

---

## New endpoints (Handrail :8011)

| Endpoint | Description |
|----------|-------------|
| `GET /transitions/latest` | 10 most recent transitions, newest-first |
| `GET /transitions/{transition_id}` | Single transition by TRN-XXXXXXXX |
| `GET /state/summary` | Aggregate state across all domains |
| `GET /state/deltas/latest` | 10 most recent TypedStateDeltas |

---

## Founder Console v9

Added **STATE REGULATION** panel — shows:
- Total transitions, deltas, sovereign count
- Domain breakdown (epistemic/operational/constitutional/commercial)
- 3 most recent transitions with surface + objective
- Refreshes every 30 seconds

---

## Ring Completion

Ring 5 (Production) remains blocked on Stripe LLC verification, live keys, and custom DNS.

The software layer is now complete through Constitutional Regulation Engine v1.
