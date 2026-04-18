# NS∞ (NorthStar Infinity) — MASTER Implementation Prompt
**AXIOLEV Holdings LLC © 2026**
**Author:** axiolevns <axiolevns@axiolev.com>
**Repo:** mkaxiolev-max/handrail, branch `boot-operational-closure`
**Package root:** `ns/` per ns_scaffold.zip — DO NOT relocate.

## Locked Ontology (ENFORCE THROUGHOUT ALL PHASES)

**10-Layer Stack:**
- L1 Constitutional: Dignity Kernel, Sentinel Gate, Constitutional Canon, Canon Barrier
- L2 Gradient: Gradient Field (was "Ether" — deprecated)
- L3 Intake: Epistemic Envelope, admissibility predicates
- L4 Conversion: The Loom (reflector functor GradientField → Canon)
- L5 Semantic: Alexandrian Lexicon (was "Lexicon"/"Atomlex" — deprecated)
- L6 State: State Manifold (was "Manifold" alone — deprecated)
- L7 Memory: Alexandrian Archive (was "Alexandria" alone — deprecated)
- L8 Lineage: Lineage Fabric (was "CTF" — deprecated)
- L9 Error & Correction: HIC, PDP, supersession routers
- L10 Narrative & Interface: Ω-Link Narrative Interface, Violet Interface
  (layer name "Narrative"; Storytime retained ONLY as service module name)

**10 Invariants (honor in every phase):**
- I1 Canon precedes Conversion
- I2 Append-only memory (Lineage inertness)
- I3 No LLM authority over Canon
- I4 Hardware quorum on canon changes (YubiKey 26116460 mandatory)
- I5 Provenance inertness (cryptographic hash-chain)
- I6 Sentinel Gate soundness
- I7 Bisimulation with replay (2-safety)
- I8 Distributed eventual consistency (CRDT/SEC)
- I9 Hardware quorum for authority change (Byzantine ≥2f+1)
- I10 Supersession monotone (never delete)

**Doctrinal partition:**
Models propose, NS decides, Violet speaks, Handrail executes,
Alexandrian Archive remembers. L10 may NEVER amend L1–L9.
LLMs are bounded L6 components and never define truth or state.

---

# PHASE A — T1 RINGS 1-6

## Ring 1 — L1 Constitutional Layer + I1–I10
**Paths:**
- `ns/domain/models/constitutional.py` — ConstraintClass enum (SACRED, RELAXABLE),
  ConstitutionalRule, DignityCheck, SentinelGateDecision
- `ns/domain/models/sacred.py` — 7 sacred rules (all SACRED):
  dignity_kernel, append_only_lineage, receipt_requirement,
  no_unauthorized_canon, no_deletion_rewriting, no_identity_falsification,
  truthful_provenance
- `ns/domain/models/invariants.py` — I1..I10 exported as checkable predicates

**Test:** `ns/tests/test_ring1_constitutional_layer.py`
**Tag:** `ring-1-constitutional-layer-v1`

## Ring 2 — L5/L6/L7/L8 substrate
**Paths:**
- `ns/integrations/alexandrian_archive.py` (rename/alias from alexandria.py)
- `ns/integrations/alexandrian_lexicon.py` (NEW)
- `ns/integrations/state_manifold.py` (NEW)
- `ns/integrations/lineage_fabric.py` (NEW)

Storage on `/Volumes/NSExternal/ALEXANDRIA/`:
```
branches/<branch_id>.json
projections/<projection_id>.json
canon/rules.jsonl
ledger/ns_events.jsonl
lexicon/baptisms.jsonl
lexicon/supersessions.jsonl
state/shards/<shard_id>/deltas.jsonl
state/shards/<shard_id>/manifest.json
state/transitions/
narrative/
cqhml/
```
Append-only (I2), SHA-256 hash-chain (I5), fsync, fcntl.flock, supersession
only (I10), Alexandrian Lexicon baptism receipts.

**Test:** `ns/tests/test_ring2_substrate_layers.py`
**Tag:** `ring-2-substrate-layers-v1`

## Ring 3 — L4 The Loom
**Paths:** `ns/services/loom/service.py`, `ns/services/loom/mode_switching.py`

Reflector functor L : GradientField → Canon. ConfidenceEnvelope:
```
score = 0.45*evidence + 0.25*(1 - contradiction) + 0.15*novelty + 0.15*stability
```
(weights exact, sum = 1.0).

Loop: generate → test → contradict → reweight → narrate → store → re-enter.

**Test:** `ns/tests/test_ring3_loom.py`
**Tag:** `ring-3-loom-v1`

## Ring 4 — L3 Intake + Canon Promotion Gate
**Paths:**
- `ns/services/canon/service.py`
- `ns/services/canon/promotion_guard.py`
- `ns/services/canon/relation_binding.py`
- `ns/api/routers/canon.py` (POST /canon/promote)

Six-condition gate + I1 + I4:
1. confidence.score() ≥ 0.82
2. contradiction_weight ≤ 0.25
3. reconstructability ≥ 0.90
4. lineage_valid(branch) == True
5. HIC approval receipt present
6. PDP approval receipt present
Plus Lineage Fabric receipt written, I1 (Canon-before-Conversion), I4
(hardware quorum with YubiKey 26116460 as mandatory singleton Byzantine
≥2f+1 signer).

```python
def verify_hardware_quorum(quorum_certs: list[dict]) -> bool:
    yubi_present = any(c.get("serial") == "26116460" for c in quorum_certs)
    f = (len(quorum_certs) - 1) // 3
    return yubi_present and len(quorum_certs) >= 2*f + 1
```

Receipts emitted:
- `canon_promoted_with_hardware_quorum` on success
- `canon_promotion_denied_i9_quorum_missing` on failure

**Test:** `ns/tests/test_ring4_canon_promotion.py`
**Tag:** `ring-4-canon-promotion-v1`

## Ring 5 — External Gates (noted, out-of-band)
**Path:** `ns/domain/policies/external_gates.py`
```python
EXTERNAL_GATES = [
    {"id": "stripe_llc_verification", "status": "pending", "note": "out-of-band"},
    {"id": "stripe_live_keys_vercel", "status": "pending", "note": "out-of-band"},
    {"id": "root_handrail_price_ids", "status": "pending", "note": "out-of-band"},
    {"id": "yubikey_slot2", "status": "pending", "note": "~$55 procurement"},
    {"id": "dns_cname_root", "status": "pending",
     "note": "root.axiolev.com -> root-jade-kappa.vercel.app"},
]
```
No network calls.

**Test:** `ns/tests/test_ring5_external_gates_noted.py`
**Tag:** `ring-5-external-gates-noted-v1`

## Ring 6 — G₂ 3-form invariant ∇φ=0
**Path:** `ns/domain/models/g2_invariant.py` (T3/T4 import from this).

Fano plane (standard order): φ = e^123 + e^145 + e^167 + e^246 + e^257 + e^347 + e^356

```python
FANO_TRIPLES = ((1,2,3),(1,4,5),(1,6,7),(2,4,6),(2,5,7),(3,4,7),(3,5,6))
def phi_components() -> tuple: return FANO_TRIPLES
def nabla_phi_zero(state) -> bool: ...
def ring6_phi_parallel(state) -> bool: return nabla_phi_zero(state)
```

Ring 4 canon promotion MUST call `ring6_phi_parallel(state)`.
Receipt: `ring6_g2_invariant_checked`.

**Test:** `ns/tests/test_ring6_g2_invariant.py`
**Tag:** `ring-6-g2-invariant-v1`

---

# PHASE B — T2 NCOM/PIIC + FOUNDER CONSOLE (worktree feature/ncom-piic-v2)

## B1 doctrine-scaffold
Create `docs/doctrine/NCOM_PIIC_DOCTRINE.md` (Krishnamurti-aligned synthesis).
Add I12..I15 as sibling invariants.

**Tag:** `ncom-piic-doctrine-v2`

## B2 ncom-runtime
- `ns/services/ncom/__init__.py`
- `ns/services/ncom/state.py` — 8-state machine (inactive / priming /
  observing / branching / stabilizing / ready_for_collapse /
  forced_collapse / aborted)
- `ns/services/ncom/readiness.py` — CollapseReadiness (ERS, CRS, IPI,
  contradictionPressure, branchDiversityAdequacy, hardVetoes, recommendedAction)

**Tag:** `ncom-runtime-v2`

## B3 piic-chain
- `ns/services/piic/__init__.py`
- `ns/services/piic/chain.py` — monotonic forward progression with stage
  gates (perception → interpretation → identification → commitment)

**Tag:** `piic-chain-v2`

## B4 pi-gate-integration
Extend `ns/services/canon/promotion_guard.py` to require at promotion time:
- NCOM state in {ready_for_collapse, forced_collapse}
- PIIC stage == commitment
- readiness.recommendedAction == "collapse"
- hardVetoes == []

Receipt: `ncom_veto_emitted` when vetoed.

**Tag:** `ncom-pi-gate-v2`

## B5 founder-console-api
Extend `ns/api/routers/ui_runtime.py` with:
- GET /founder-console/snapshot
- GET /founder-console/history
- GET /founder-console/contradictions/active
- GET /founder-console/observations/open
- GET /founder-console/routing/current
- GET /founder-console/receipts/recent

Schemas: `ns/api/schemas/ncom_piic.py` (NEW).
Receipt names added: `ncom_state_transitioned`, `piic_stage_advanced`, `ncom_veto_emitted`.

**Tag:** `founder-console-api-v2`

## B6 founder-console-ui
Populate `ns/services/ui/engine_room.py`, `living_architecture.py`,
`runtime_panels.py`, `websocket_events.py`. Live-fetch snapshot from
`/founder-console/snapshot`. Render NCOM state pill, PIIC stage chain,
IPI/ERS/CRS gauges, contradiction list, top interpretation.

**Tag:** `founder-console-ui-v2`

## B7 tests-and-proof
- `ns/tests/test_ncom.py` (state transitions + readiness vetoes + collapse gate)
- `ns/tests/test_piic.py` (monotonic advance + no-skip + gate-on-NCOM)
- Proof: `proofs/ncom/ncom_piic_proof_v2.json`

**Tag:** `ncom-piic-tests-green-v2`

---

# PHASE C — T3 RIL + ORACLE v2 (worktree feature/ril-oracle-v2)

## C1 doctrine-scaffold
`docs/doctrine/RIL_ORACLE_DOCTRINE.md` — seven integrity engines, two-stage
adjudication, precedence ladder. Add I16..I20 extension invariants.

**Tag:** `ril-oracle-doctrine-v2`

## C2 ril-pydantic-models
Populate:
- `ns/domain/models/integrity.py` (full model)
- `ns/api/schemas/ril.py`
- `ns/api/schemas/common.py` (IntegrityRouteEffect, RouteIntent,
  ReflexiveIntegrityState, IntegritySummary)

**Tag:** `ril-models-v2`

## C3 ril-engines (8 scaffold files)
- `ns/services/ril/drift_engine.py`
- `ns/services/ril/grounding_engine.py`
- `ns/services/ril/commitment_engine.py`
- `ns/services/ril/encounter_engine.py`
- `ns/services/ril/founder_loop_breaker.py`
- `ns/services/ril/reality_binding_engine.py`
- `ns/services/ril/rendering_capture.py`
- `ns/services/ril/interface_recalibration.py`

**Tag:** `ril-engines-v2`

## C4 ril-evaluator
Populate `ns/services/ril/service.py` (compose all 8 engines).

**Tag:** `ril-evaluator-v2`

## C5 oracle-v2-contract
Populate `ns/api/schemas/oracle.py`:
OracleDecision, HandrailScope, OracleSeverity, ConstitutionalContext,
OracleCondition, OracleBlockingReason, HandrailExecutionEnvelope,
OracleAdjudicationRequest, OracleAdjudicationResponse.

**Tag:** `oracle-v2-contract-v2`

## C6 oracle-v2-adjudicator
Populate `ns/services/oracle/adjudicator.py`, `service.py`,
`constitutional_overlays.py` (MUST import `ring6_phi_parallel` from
`ns.domain.models.g2_invariant`), `decision_selector.py`,
`envelope_builder.py`, `founder_translation.py`, `trace_builder.py`.

**Tag:** `oracle-v2-adjudicator-v2`

## C7 policy-matrix
Populate `ns/services/oracle/policy_matrix.py`.

**Tag:** `oracle-policy-matrix-v2`

## C8 route-integration
Populate `ns/api/routers/ril.py` and `ns/api/routers/oracle.py`.

**Tag:** `ril-oracle-bridge-v2`

## C9 tests-and-proofs
- `ns/tests/test_ril_engines.py` (≥6 tests)
- `ns/tests/test_oracle_v2.py` (≥5 tests)
- Proof: `proofs/ril/ril_oracle_proof_v2.json`

**Tags:** `ril-oracle-tests-green-v2`, umbrella `ril-oracle-v2`, merge tag `ril-oracle-merged-v2`.

---

# PHASE D — T1 RING 7 FINAL CERTIFICATION

**Path:** `ns/services/canon/final_cert.py`

1. Verify tags `ncom-piic-merged-v2` and `ril-oracle-merged-v2` exist.
2. Verify feature branches `feature/ncom-piic-v2` and `feature/ril-oracle-v2`.
3. Run full `ns/tests/` suite (must be green).
4. Emit umbrella tag `ns-infinity-cqhml+ncom+ril-v1.0.0`.
5. Emit founder-grade tag `ns-infinity-founder-grade-<YYYYMMDD>`.

**Test:** `ns/tests/test_ring7_final_cert.py`
**Tag:** `ring-7-final-cert-v1`

---

# PHASE E — T4 CQHML MANIFOLD ENGINE (worktree feature/cqhml-manifold-v2)

## E1 doctrine-scaffold
`docs/doctrine/CQHML_MANIFOLD_DOCTRINE.md`.

**Tag:** `cqhml-manifold-doctrine-v2`

## E2 dimensions-pydantic-models
`ns/api/schemas/cqhml.py` (NEW):
DimensionalCoordinate, SemanticMode, PolicyMode, ObserverFrame,
DimensionalEnvelope, ProjectionRequest, ProjectionResult.

**Tag:** `cqhml-dimensions-v2`

## E3 cqhml-quaternion-core
`ns/services/cqhml/quaternion.py` (pure NumPy).

**Tag:** `cqhml-quaternion-core-v2`

## E4 cqhml-story-atom-loom
`ns/services/cqhml/story_atom_loom.py`.

**Tag:** `cqhml-story-atom-loom-v2`

## E5 dimensional-contradiction-engine
`ns/services/cqhml/contradiction_engine.py`.

**Tag:** `cqhml-contradiction-engine-v2`

## E6 dimensional-projection-service
`ns/services/cqhml/projection_service.py`.

**Tag:** `cqhml-projection-service-v2`

## E7 spin7-cayley-phi
`ns/domain/models/spin7_invariant.py`.

**Tag:** `cqhml-spin7-phi-v2`

## E8 omega-manifold-router
`ns/services/omega/manifold_router.py`.

**Tag:** `cqhml-omega-router-v2`

## E9 oracle-dimensional-gate
`ns/services/oracle/dimensional_gate.py`.

**Tag:** `cqhml-oracle-dim-gate-v2`

## E10 tests-and-proofs (>=24 tests)
`ns/tests/test_cqhml_*.py` (8 files).
Proof: `proofs/cqhml/cqhml_manifold_proof_v2.json`.

**Tags:** `cqhml-manifold-tests-green-v2`, umbrella `cqhml-manifold-v2`,
merge tag `cqhml-manifold-merged-v2`, final tag `ns-infinity-manifold-complete-v1.0.0`.

---

## Commit & tag conventions
- Author via `-c user.name/email` (axiolevns / axiolevns@axiolev.com)
- Commit: `<phase-id>: <desc> green — AXIOLEV Holdings LLC © 2026`
- Master never force-pushes.
