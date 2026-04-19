# NS∞ Live Ontology Audit — 20260419T232440Z

AXIOLEV Holdings LLC © 2026

Locked 10-layer ontology is enforced. Deprecated names are flagged.

## Layers and actual locations

| # | Canonical Name | Actual Paths (matched) |
|---|----------------|------------------------|
| L1 | Constitutional Layer | .terminal_manager/packets/outbox/P1_live_reprove_20260417T004910Z.md .terminal_manager/state/state_20260416T233746Z.md .terminal_manager/state/state_20260416T234033Z.md ARCHITECTURE_TRUTH.md artifacts/ontology_audit_20260419T231841Z.md AXIOLEV_STATE.md CHANGELOG.md CLAUDE.md dignity_kernel/dignity_kernel.py FINAL_STATE.md FOUNDER_OPERATIONS_MANUAL.md LEXICON_INTEGRATION.md  |
| L2 | Gradient Field | artifacts/ontology_audit_20260419T224057Z.md artifacts/ontology_audit_20260419T231841Z.md artifacts/ui_addition_20260419T231841Z.md CLOSURE_PROMPT.md docs/doctrine/RIL_ORACLE_DOCTRINE.md ns/api/routers/ui_runtime.py ns/api/schemas/cqhml.py ns/domain/models/integrity.py ns/domain/models/invariants.py ns/integrations/ether.py ns/services/cqhml/contradiction_engine.py ns/services/cqhml/projection_service.py  |
| L3 | Epistemic Envelope | artifacts/ontology_audit_20260419T224057Z.md artifacts/ontology_audit_20260419T231841Z.md CLOSURE_PROMPT.md ns/api/schemas/cqhml.py ns/services/ui/router.py PROMPT.md  |
| L4 | The Loom | artifacts/ontology_audit_20260419T224057Z.md artifacts/ontology_audit_20260419T231841Z.md CLOSURE_PROMPT.md ns/api/schemas/cqhml.py ns/domain/receipts/names.py ns/services/cqhml/story_atom_loom.py ns/services/loom/mode_switching.py ns/services/loom/service.py ns/services/ui/living_architecture.py ns/services/ui/router.py ns/tests/test_ring3_loom.py PROMPT.md  |
| L5 | Alexandrian Lexicon | artifacts/ontology_audit_20260419T224057Z.md artifacts/ontology_audit_20260419T231841Z.md artifacts/ui_addition_20260419T231841Z.md CLOSURE_PROMPT.md ns/api/schemas/cqhml.py ns/domain/models/omega_primitives.py ns/integrations/alexandria.py ns/services/cqhml/contradiction_engine.py ns/services/cqhml/projection_service.py ns/services/omega/manifold_router.py ns/services/oracle/dimensional_gate.py ns/services/ui/living_architecture.py  |
| L6 | State Manifold | artifacts/ontology_audit_20260419T224057Z.md artifacts/ontology_audit_20260419T231841Z.md CLOSURE_PROMPT.md docs/doctrine/RIL_ORACLE_DOCTRINE.md ns/api/schemas/cqhml.py ns/domain/models/invariants.py ns/domain/models/omega_primitives.py ns/integrations/alexandria.py ns/services/cqhml/contradiction_engine.py ns/services/cqhml/projection_service.py ns/services/omega/manifold_router.py ns/services/oracle/dimensional_gate.py  |
| L7 | Alexandrian Archive | artifacts/ontology_audit_20260419T224057Z.md artifacts/ontology_audit_20260419T231841Z.md artifacts/ui_addition_20260419T231841Z.md certification/NS_CLOSURE_MAX_v1.md certification/NS_CLOSURE_MAX_v2.md CLOSURE_PROMPT.md docs/doctrine/RIL_ORACLE_DOCTRINE.md ns/api/schemas/cqhml.py ns/domain/models/invariants.py ns/domain/models/omega_primitives.py ns/integrations/alexandria.py ns/integrations/omega_store.py  |
| L8 | Lineage Fabric | .terminal_manager/logs/master_return_20260418T231155Z.md .terminal_manager/logs/master_return_20260418T233039Z.md artifacts/ontology_audit_20260419T224057Z.md artifacts/ontology_audit_20260419T231841Z.md artifacts/ui_addition_20260419T231841Z.md CLOSURE_PROMPT.md ns/api/routers/omega.py ns/api/routers/ui_runtime.py ns/api/schemas/cqhml.py ns/domain/models/invariants.py ns/domain/models/omega_primitives.py ns/domain/models/spin7_invariant.py  |
| L9 | HIC / PDP | .runs/COMPLETION_RECEIPT.md ADAPTER_COMPLETE.md ARCHITECTURE_TRUTH.md artifacts/ontology_audit_20260419T224057Z.md artifacts/ontology_audit_20260419T231841Z.md AXIOLEV_STATE.md certification/FOUNDER_READY_PLUS_v1.md CHANGELOG.md CLOSURE_PROMPT.md COMPLETION_RECEIPT.md docs/COMMIT_STANDARD.md FINAL_STATE.md  |
| L10 | Narrative + Interface | .runs/COMPLETION_RECEIPT.md .terminal_manager/state/state_20260416T233746Z.md .terminal_manager/state/state_20260416T234033Z.md apps/ns-tauri/src-tauri/target/release/build/markup5ever-4e16feff0fd849b3/out/named_entities.rs ARCHITECTURE_TRUTH.md artifacts/mac_app_wrap_audit.md artifacts/ontology_audit_20260419T224057Z.md artifacts/ontology_audit_20260419T231841Z.md AXIOLEV_STATE.md certification/FOUNDER_READY_PLUS_v1.md certification/NS_CLOSURE_MAX_v1.md certification/NS_CLOSURE_MAX_v2.md  |

## Deprecated-name audit

### Deprecated: `Atomlex`
```
./ns/tests/test_ring2_substrate_layers.py:266:        archive.baptize("Alexandrian Lexicon", "L5 layer (formerly Atomlex)", "PROMPT.md")
./services/ns/nss/ui/founder.py:228:    <!-- Atomlex Engine -->
./services/ns/nss/ui/founder.py:782:// ── Atomlex Engine ──
./services/ns/nss/ui/founder.py:783:async function refreshAtomlex() {
./services/ns/nss/ui/founder.py:1048:      <div class="hrow"><div class="hk">Lexicon</div><div class="hv"><span style="color:var(--ok)">${r.lexicon?.entry_count||0}</span> entries · Atomlex <span style="color:var(--bl)">${r.atomlex?.nodes||0}</span> nodes</div></div>
./services/ns/nss/ui/founder.py:1074:refreshAtomlex();
./services/ns/nss/ui/founder.py:1086:setInterval(refreshAtomlex, 120000);
./services/ns/nss/api/server.py:3635:    # ── Atomlex Constraint Graph Proxy ────────────────────────────────────────
./services/ns/nss/api/server.py:3639:        """Proxy to Atomlex graph status — node/edge count."""
./services/ns/nss/api/server.py:3649:        """Proxy to Atomlex word query — full constraint propagation."""
./services/ns/nss/api/server.py:3659:        """Proxy to Atomlex analyze — constitutional vocabulary analysis."""
./services/handrail/handrail/server.py:704:    # --- Atomlex (proxy call) ---
./services/atomlex/server.py:2:Atomlex v4.0 — Constraint Semantic Graph Engine
./services/atomlex/server.py:25:app = FastAPI(title="Atomlex v4.0", version="4.0.0")
./services/atomlex/server.py:278:        return JSONResponse({"ok": False, "error": f"word '{word}' not in Atomlex graph"}, status_code=404)
./services/atomlex/atomlex/server.py:2:Atomlex v4.0 — Constraint Semantic Graph Engine
./services/atomlex/atomlex/server.py:25:app = FastAPI(title="Atomlex v4.0", version="4.0.0")
./services/atomlex/atomlex/server.py:278:        return JSONResponse({"ok": False, "error": f"word '{word}' not in Atomlex graph"}, status_code=404)
./services/atomlex/atomlex/graph_engine.py:2:Atomlex Graph Engine v4.0
```

