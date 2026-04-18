# NS∞ (NorthStar Infinity) — Master Implementation Prompt  v3

**AXIOLEV Holdings LLC © 2026** — axiolevns <axiolevns@axiolev.com>
**Repo:** mkaxiolev-max/handrail, branch `boot-operational-closure`
**Runtime root:** `~/axiolev_runtime`
**Alexandrian Archive:** `/Volumes/NSExternal/ALEXANDRIA`

This is the canonical specification for Terminal 1 (T1). T1 builds **Rings 1–6**
under the scaffolded `ns/` package, then performs **Ring 7 final certification**
after Terminal 2 (NCOM/PIIC) and Terminal 3 (RIL/ORACLE) have auto-merged.

## Locked ontology (Research_Report.pdf)

- L1 Constitutional Layer — Dignity Kernel, Sentinel Gate, Constitutional Canon, Canon Barrier
- L2 Gradient Layer — Gradient Field (formerly "Ether")
- L3 Intake Layer — Epistemic Envelope
- L4 Conversion Layer — The Loom
- L5 Semantic Layer — Alexandrian Lexicon (formerly "Lexicon/Atomlex")
- L6 State Layer — State Manifold (formerly "Manifold")
- L7 Memory Layer — Alexandrian Archive (formerly "Alexandria")
- L8 Lineage Layer — Lineage Fabric (formerly "CTF")
- L9 Error & Correction Layer — HIC, PDP, divergence/supersession
- L10 Narrative & Interface Layer — Ω-Link, Violet (layer name = Narrative;
       Storytime retained only as service module name per scaffold)

Never use deprecated names in code or docs.

## Ten invariants (I1..I10)

- I1  Canon precedes Conversion  (Ring 4 gate)
- I2  Append-only memory (Lineage inertness)  (Ring 2 writer)
- I3  No LLM authority over Canon
- I4  Hardware quorum on canon changes — YubiKey serial 26116460 mandatory
- I5  Provenance inertness (hash-chain)
- I6  Sentinel Gate soundness
- I7  Bisimulation with replay (2-safety)
- I8  Distributed eventual consistency (CRDT/SEC)
- I9  Hardware quorum for authority change (≥2f+1 w/ YubiKey 26116460 mandatory)
- I10 Supersession monotone (never-delete, supersede only)

LTL/TLA+ forms:
- I1:  G(emit(o) ⇒ (∃c : canon_committed(c) S emit(o)) ∧ c ⊨ o.spec)
- I2:  G(lineage = ℓ ⇒ X(Prefix(ℓ, lineage)))
- I5:  ∀i : lineage[i].id = Hash(lineage[i].content, prev_id)
- I6:  G(executed(a) ⇒ CB(canon)(a) = ⊤)
- I7:  ∀s1,s2 : lineage(s1)=lineage(s2) ⇒ Obs(s1) ~ Obs(s2)
- I10: canon ⊑ canon' ∧ ImmutableAxioms(canon) ⊆ canon'

## Scaffold floor (paths are exact)

```
ns/
  api/
    server.py
    deps/{config.py, receipts.py}
    routers/{health.py, ril.py, oracle.py, handrail.py, canon.py,
             storytime.py, ui_runtime.py}
    schemas/{common.py, canon.py, handrail.py, omega.py, oracle.py,
             ril.py, storytime.py, ui_runtime.py}
  domain/
    models/{integrity.py, g2_invariant.py (T1 Ring 6), spin7_invariant.py (T4)}
    receipts/{emitter.py, names.py, store.py}
  integrations/{alexandria.py (alias alexandrian_archive),
                ether.py (alias gradient_field),
                handrail_transport.py, hic.py, model_router.py, pdp.py}
  services/
    canon/{service.py, promotion_guard.py, relation_binding.py}
    handrail/{service.py, action_runner.py, envelope_guard.py,
              observation_runner.py, probe_runner.py, reconcile_callback.py}
    loom/{service.py, mode_switching.py}
    omega/{service.py, packet_builder.py}
    oracle/{service.py, adjudicator.py, constitutional_overlays.py,
            decision_selector.py, envelope_builder.py, founder_translation.py,
            policy_matrix.py, trace_builder.py}
    ril/{service.py, commitment_engine.py, drift_engine.py,
         encounter_engine.py, founder_loop_breaker.py, grounding_engine.py,
         interface_recalibration.py, reality_binding_engine.py,
         rendering_capture.py}
    storytime/{service.py, founder_view.py, humility_mode.py,
               narrative_trace.py}
    ui/{service.py, engine_room.py, living_architecture.py,
        runtime_panels.py, websocket_events.py}
  tests/{test_smoke.py, plus per-ring/per-packet tests added}
```

## Ownership (do NOT cross)

- T1 owns Rings 1–7 (this prompt)
- T2 owns NCOM/PIIC under `ns/services/ncom/` and `ns/services/piic/`
- T3 owns RIL + ORACLE v2 — populates the scaffold's existing files
- T4 owns CQHML/Manifold + 5D–11D under `ns/services/cqhml/` and
      `ns/domain/models/spin7_invariant.py`

Claude Code in T1 must NOT implement NCOM, PIIC, RIL, ORACLE, or CQHML work.
Limit all edits to the Ring scope described below.

## Ring 1 — L1 Constitutional Layer

Modules:
- `ns/api/schemas/canon.py` — `ConstraintClass(SACRED|RELAXABLE)`,
  `ConstitutionalRule`, `DignityCheck`, `NeverEvent`
- `ns/services/canon/service.py` — initial stub loads seven sacred constraints:
  dignity_kernel, append_only_lineage, receipt_requirement,
  no_unauthorized_canon, no_deletion_rewriting, no_identity_falsification,
  truthful_provenance
- `ns/services/canon/promotion_guard.py` — bare-minimum stub (Ring 4 fills it)
- `ns/domain/models/integrity.py` — basic types used across rings

Integration test: `ns/tests/test_ring1_constitutional_layer.py`
Tag: `ring1-constitutional-layer-v1`

## Ring 2 — Substrate (L5/L6/L7/L8)

Alexandrian Archive layout on `/Volumes/NSExternal/ALEXANDRIA/`:
```
branches/<branch_id>.json
projections/<projection_id>.json
canon/rules.jsonl              (append-only)
ledger/ns_events.jsonl         (append-only Lineage Fabric)
lexicon/baptisms.jsonl         (append-only Alexandrian Lexicon)
lexicon/supersessions.jsonl    (append-only)
state/shards/<id>/deltas.jsonl (append-only)
state/shards/<id>/manifest.json
state/transitions/
narrative/
cqhml/                         (T4 adds)
```

Modules to populate:
- `ns/integrations/alexandria.py` — expose `alexandrian_archive` as alias
- `ns/integrations/ether.py` — expose `gradient_field` as alias
- `ns/domain/receipts/emitter.py` — fsync'd append-only JSONL writer
- `ns/domain/receipts/store.py` — hash-chain reader
- `ns/domain/receipts/names.py` — extend authoritative set (see below)

Authoritative receipt names (extend, do not remove):
```
ril_evaluation_started
ril_drift_checked
ril_grounding_checked
ril_encounter_interrupt_triggered
ril_reality_binding_checked
ril_route_effects_emitted
oracle_received_ril_packet
oracle_adjudicated_with_integrity_state
oracle_handrail_envelope_built
storytime_humility_entered
interface_recalibration_entered
interface_recalibration_completed
handrail_scope_narrowed_by_ril
ring6_g2_invariant_checked                    (added by T1)
canon_promoted_with_hardware_quorum           (added by T1)
canon_promotion_denied_i9_quorum_missing      (added by T1)
lineage_fabric_appended                       (added by T1)
alexandrian_lexicon_baptism_receipted         (added by T1)
alexandrian_lexicon_drift_blocked             (added by T1)
narrative_emitted_with_receipt_hash           (added by T1)
dimensional_contradiction_detected            (added by T4)
manifold_projection_lawful                    (added by T4)
```

Integration test: `ns/tests/test_ring2_substrate_layers.py`
Tag: `ring2-substrate-layers-v1`

## Ring 3 — L4 The Loom

Modules:
- `ns/services/loom/service.py` — reflector functor L: Gradient → Canon with
  `apply(gradient_triple, canon) -> proposition_with_provenance`
- `ns/services/loom/mode_switching.py` — deterministic mode selection

I7 bisimulation test: running the same lineage prefix twice must produce
bisimilar observations.

Integration test: `ns/tests/test_ring3_loom.py`
Tag: `ring3-loom-v1`

## Ring 4 — L3 Intake + Canon promotion gate

Modules:
- `ns/api/routers/canon.py` — POST /canon/promote
- `ns/services/canon/service.py` — `promote(branch_id, context)`
- `ns/services/canon/promotion_guard.py` — gate logic

Gate — ALL six conditions must hold:
1. `confidence.score() >= 0.82`
2. `contradiction_weight <= 0.25`
3. `reconstructability >= 0.90`
4. `lineage_valid(branch)` is True
5. `HIC.approves` is True
6. `PDP.approves` is True
7. Lineage Fabric receipt is written (`canon_promoted_with_hardware_quorum`)
8. I1: candidate branch must have commitIdx of a canon axiom < emit-tick
9. I4/I9: QuorumCert(YubiKey 26116460) mandatory; 2f+1 validators

If I9 quorum missing → emit `canon_promotion_denied_i9_quorum_missing` and
return structured error `{"error":"I9_QUORUM_MISSING"}`.

Integration test: `ns/tests/test_ring4_canon_promotion.py`
Tag: `ring4-canon-promotion-v1`

## Ring 5 — External gates (noted)

`ns/services/canon/relation_binding.py` or a new `ns/domain/policies/external_gates.py`
declares the pending external gates without performing network calls:
```
stripe_llc_verification          pending
stripe_live_keys_vercel          pending
root_handrail_price_ids          pending
yubikey_slot2                    pending  (~$55 procurement)
dns_cname_root                   pending  (root.axiolev.com → Vercel)
```

Integration test: `ns/tests/test_ring5_external_gates_noted.py`
Tag: `ring5-external-gates-noted-v1`

## Ring 6 — G₂ 3-form invariant

`ns/domain/models/g2_invariant.py` — exact surface T3/T4 will import:
```python
FANO_TRIPLES = (
    (1,2,3),(1,4,5),(1,6,7),(2,4,6),(2,5,7),(3,4,7),(3,5,6),
)
def phi_components() -> tuple: return FANO_TRIPLES
def nabla_phi_zero(state) -> bool: ...
def ring6_phi_parallel(state) -> bool:
    return nabla_phi_zero(state)
```

Every canonical promotion in Ring 4 must call `ring6_phi_parallel(state)` and
refuse promotion if False. Emit receipt `ring6_g2_invariant_checked`.

Integration test: `ns/tests/test_ring6_g2_invariant.py`
Tag: `ring6-g2-invariant-v1`

## Ring 7 — Final certification

T1 will:
1. Wait for BOTH signals: `ncom_piic_complete.signal`, `ril_oracle_complete.signal`
2. `git fetch --all --tags && git checkout ${BRANCH_MAIN} && git pull --ff-only`
3. Verify merge tags: `ncom-piic-merged-v2`, `ril-oracle-merged-v2`
4. Verify feature branches: `feature/ncom-piic-v2`, `feature/ril-oracle-v2`
5. Run FULL `ns/tests/` integration suite
6. Tag `ns-infinity-cqhml+ncom+ril-v1.0.0` (umbrella)
7. Tag `ns-infinity-founder-grade-<YYYYMMDD>` (founder)
8. Emit `build_complete` Lineage Fabric receipt

Integration test: `ns/tests/test_ring7_final_cert.py`
Tag: `ring7-final-cert-v1`

## Conventions

- Author every commit via `git -c user.name=axiolevns -c user.email=axiolevns@axiolev.com commit`
- Commit message: `ring-N: <description> green — AXIOLEV © 2026`
- Per-ring tag: `ringN-<kebab>-v1`
- Ring 7 special: `ring7-final-cert-v1`
- All timestamps UTC ISO-8601
- Pydantic v2 everywhere (`model_config = ConfigDict(extra="forbid")`)
- No print() in library code; use `structlog` if adding logging

## Ownership guardrails

Do NOT create or modify files under any of these paths — those belong to
other terminals:
- `ns/services/ncom/*`          (T2)
- `ns/services/piic/*`          (T2)
- `ns/services/cqhml/*`         (T4)
- `ns/domain/models/spin7_invariant.py`  (T4)
- `ns/services/omega/manifold_router.py` (T4)
- `ns/services/oracle/dimensional_gate.py` (T4)

For RIL/ORACLE scaffolded files, populate ONLY a minimal stub sufficient for
Ring 1–4 imports; T3 will fill bodies.

