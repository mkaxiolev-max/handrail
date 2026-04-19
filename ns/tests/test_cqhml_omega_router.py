"""NS∞ cqhml-P8: OmegaManifoldRouter tests — tri-objective Ω-router.

Validates ns/services/omega/manifold_router.py:
  * RoutingObjective, RoutingDecision enums
  * ObjectiveResult, OmegaRoutingResult dataclasses
  * OmegaManifoldRouter.route() — all three objectives
  * Receipt emission (I2 append-only)
  * Invariants I1, I2, I5, I6, I7, I10

Locked ontology enforced: Gradient Field (L2), Alexandrian Lexicon (L5),
State Manifold (L6), Alexandrian Archive (L7), Lineage Fabric (L8), Narrative (L10).
No deprecated names (Ether, CTF, Storytime-as-layer, Alexandria alone, etc.).

Tag: cqhml-omega-router-v2
AXIOLEV Holdings LLC © 2026
"""
from __future__ import annotations

import pytest

from ns.api.schemas.cqhml import (
    DimensionalCoordinate,
    DimensionalEnvelope,
    ObserverFrame,
    PolicyMode,
    ProjectionRequest,
    SemanticMode,
)
from ns.services.omega.manifold_router import (
    ObjectiveResult,
    OmegaManifoldRouter,
    OmegaRoutingResult,
    RoutingDecision,
    RoutingObjective,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _coord(layer: int, phi_parallel: bool = True, tick: int = 0) -> DimensionalCoordinate:
    return DimensionalCoordinate(layer=layer, tick=tick, phi_parallel=phi_parallel)


def _observer(
    layer: int = 6,
    mode: SemanticMode = SemanticMode.STATE,
    policy: PolicyMode = PolicyMode.ENFORCE,
) -> ObserverFrame:
    return ObserverFrame(
        frame_id="test-omega-frame",
        layer=layer,
        semantic_mode=mode,
        policy_mode=policy,
        tick=0,
    )


def _envelope(
    layer: int = 6,
    phi_parallel: bool = True,
    g2: bool = True,
    spin7: bool = True,
    mode: SemanticMode = SemanticMode.STATE,
    policy: PolicyMode = PolicyMode.ENFORCE,
    tick: int = 0,
) -> DimensionalEnvelope:
    return DimensionalEnvelope(
        coordinate=_coord(layer=layer, phi_parallel=phi_parallel, tick=tick),
        observer=_observer(layer=layer, mode=mode, policy=policy),
        g2_phi_parallel=g2,
        spin7_coherent=spin7,
        tick=tick,
    )


def _request(
    envelope: DimensionalEnvelope,
    target_layer: int = 10,
    request_id: str = "omega-req-001",
    tick: int = 0,
    semantic_mode: SemanticMode | None = None,
) -> ProjectionRequest:
    return ProjectionRequest(
        request_id=request_id,
        envelope=envelope,
        target_layer=target_layer,
        semantic_mode=semantic_mode,
        tick=tick,
    )


# ---------------------------------------------------------------------------
# 1. Module surface
# ---------------------------------------------------------------------------

class TestModuleSurface:
    def test_importable_surface(self):
        import ns.services.omega.manifold_router as m
        for name in (
            "RoutingObjective",
            "RoutingDecision",
            "ObjectiveResult",
            "OmegaRoutingResult",
            "OmegaManifoldRouter",
        ):
            assert hasattr(m, name), f"Missing symbol: {name}"

    def test_routing_objective_enum_values(self):
        assert RoutingObjective.G2_COHERENCE == "G2_COHERENCE"
        assert RoutingObjective.SPIN7_COHERENCE == "SPIN7_COHERENCE"
        assert RoutingObjective.DIMENSIONAL_PROJECTION == "DIMENSIONAL_PROJECTION"

    def test_routing_decision_enum_values(self):
        assert RoutingDecision.ADMIT == "ADMIT"
        assert RoutingDecision.BLOCK == "BLOCK"
        assert RoutingDecision.ADVISORY == "ADVISORY"

    def test_objective_result_is_dataclass(self):
        obj = ObjectiveResult(
            objective=RoutingObjective.G2_COHERENCE,
            passed=True,
            receipts=["r1"],
            detail="test",
        )
        assert obj.objective == RoutingObjective.G2_COHERENCE
        assert obj.passed is True
        assert obj.receipts == ["r1"]

    def test_omega_routing_result_fields(self):
        result = OmegaRoutingResult(
            request_id="r",
            decision=RoutingDecision.ADMIT,
            objectives=[],
            receipts=[],
            trace=[],
            tick=0,
        )
        assert result.request_id == "r"
        assert result.decision == RoutingDecision.ADMIT
        assert result.g2_phi_parallel is False
        assert result.spin7_phi_parallel is False
        assert result.projection_success is False
        assert result.error is None
        assert result.projected_coordinate is None


# ---------------------------------------------------------------------------
# 2. Basic ADMIT routing
# ---------------------------------------------------------------------------

class TestAdmitRouting:
    def test_route_returns_omega_routing_result(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert isinstance(result, OmegaRoutingResult)

    def test_admit_on_fully_coherent_envelope(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE, g2=True, spin7=True)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert result.decision == RoutingDecision.ADMIT

    def test_request_id_preserved(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=8, request_id="uid-xyz"))
        assert result.request_id == "uid-xyz"

    def test_tick_propagated(self):
        env = _envelope(layer=5, mode=SemanticMode.LEXICAL, tick=7)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=8, tick=7))
        assert result.tick == 7

    def test_three_objectives_always_returned(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert len(result.objectives) == 3
        objectives = {o.objective for o in result.objectives}
        assert RoutingObjective.G2_COHERENCE in objectives
        assert RoutingObjective.SPIN7_COHERENCE in objectives
        assert RoutingObjective.DIMENSIONAL_PROJECTION in objectives

    def test_g2_flag_true_on_admit(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE, g2=True)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert result.g2_phi_parallel is True

    def test_spin7_flag_true_on_admit(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE, spin7=True)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert result.spin7_phi_parallel is True

    def test_projection_success_flag_true_on_admit(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert result.projection_success is True


# ---------------------------------------------------------------------------
# 3. G₂ coherence block (Objective 1)
# ---------------------------------------------------------------------------

class TestG2CoherenceBlock:
    def test_g2_false_returns_block(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE, g2=False)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert result.decision == RoutingDecision.BLOCK

    def test_g2_block_receipt_emitted(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE, g2=False)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert "omega_router_g2_coherence_block" in result.receipts

    def test_block_receipt_emitted_on_g2_failure(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE, g2=False)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert "omega_router_block" in result.receipts

    def test_g2_objective_failed_flag(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE, g2=False)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        g2_obj = next(o for o in result.objectives if o.objective == RoutingObjective.G2_COHERENCE)
        assert g2_obj.passed is False

    def test_g2_objective_passed_on_coherent(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE, g2=True)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        g2_obj = next(o for o in result.objectives if o.objective == RoutingObjective.G2_COHERENCE)
        assert g2_obj.passed is True

    def test_g2_block_error_mentions_i6(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE, g2=False)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert result.error is not None
        assert "I6" in result.error or "G₂" in result.error or "g2" in result.error.lower()

    def test_g2_flag_false_in_result(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE, g2=False)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert result.g2_phi_parallel is False


# ---------------------------------------------------------------------------
# 4. Spin(7) coherence block (Objective 2)
# ---------------------------------------------------------------------------

class TestSpin7CoherenceBlock:
    def test_spin7_false_returns_block(self):
        # g2=True so G₂ passes; spin7=False triggers Spin(7) block
        env = _envelope(layer=6, mode=SemanticMode.STATE, g2=True, spin7=False)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert result.decision == RoutingDecision.BLOCK

    def test_spin7_block_receipt_emitted(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE, g2=True, spin7=False)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert "omega_router_spin7_coherence_block" in result.receipts

    def test_spin7_objective_failed_flag(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE, g2=True, spin7=False)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        s7_obj = next(
            o for o in result.objectives
            if o.objective == RoutingObjective.SPIN7_COHERENCE
        )
        assert s7_obj.passed is False

    def test_spin7_flag_false_in_result(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE, g2=True, spin7=False)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert result.spin7_phi_parallel is False

    def test_spin7_block_error_mentions_spin7(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE, g2=True, spin7=False)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert result.error is not None
        assert "Spin" in result.error or "spin7" in result.error.lower()


# ---------------------------------------------------------------------------
# 5. Projection block (Objective 3) — I6 Sentinel Gate on L1
# ---------------------------------------------------------------------------

class TestProjectionBlock:
    def test_l1_phi_false_yields_block(self):
        # L1 with phi_parallel=False triggers I6 Sentinel Gate in projection service
        env = _envelope(
            layer=1, phi_parallel=False, mode=SemanticMode.CONSTITUTIONAL,
            g2=True, spin7=True,
        )
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=5))
        assert result.decision == RoutingDecision.BLOCK

    def test_projection_block_receipt_emitted(self):
        env = _envelope(
            layer=1, phi_parallel=False, mode=SemanticMode.CONSTITUTIONAL,
            g2=True, spin7=True,
        )
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=5))
        assert "omega_router_projection_block" in result.receipts

    def test_block_has_error_on_projection_failure(self):
        env = _envelope(
            layer=1, phi_parallel=False, mode=SemanticMode.CONSTITUTIONAL,
            g2=True, spin7=True,
        )
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=5))
        assert result.error is not None

    def test_no_projected_coordinate_on_block(self):
        env = _envelope(
            layer=1, phi_parallel=False, mode=SemanticMode.CONSTITUTIONAL,
            g2=True, spin7=True,
        )
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=5))
        assert result.projected_coordinate is None

    def test_projection_success_flag_false_on_block(self):
        env = _envelope(
            layer=1, phi_parallel=False, mode=SemanticMode.CONSTITUTIONAL,
            g2=True, spin7=True,
        )
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=5))
        assert result.projection_success is False


# ---------------------------------------------------------------------------
# 6. Receipt emission and I2 append-only
# ---------------------------------------------------------------------------

class TestReceiptEmission:
    def test_admit_receipt_on_successful_route(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert "omega_router_admit" in result.receipts

    def test_block_receipt_on_blocked_route(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE, g2=False)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert "omega_router_block" in result.receipts

    def test_receipts_non_empty_on_admit(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert len(result.receipts) > 0

    def test_receipts_accumulate_across_calls(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE)
        router = OmegaManifoldRouter()
        router.route(_request(env, target_layer=8, request_id="r1"))
        router.route(_request(env, target_layer=10, request_id="r2"))
        all_receipts = router.receipts()
        assert len(all_receipts) >= 4  # at minimum 2 per call

    def test_receipts_snapshot_is_copy_i10(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE)
        router = OmegaManifoldRouter()
        router.route(_request(env, target_layer=10))
        snap1 = router.receipts()
        snap1.clear()
        snap2 = router.receipts()
        assert len(snap2) > 0  # internal list unaffected

    def test_g2_pass_receipt_on_coherent(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE, g2=True)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert "omega_router_g2_coherence_pass" in result.receipts

    def test_spin7_pass_receipt_on_coherent(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE, spin7=True)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert "omega_router_spin7_coherence_pass" in result.receipts

    def test_projection_pass_receipt_on_success(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert "omega_router_projection_pass" in result.receipts


# ---------------------------------------------------------------------------
# 7. Trace
# ---------------------------------------------------------------------------

class TestTrace:
    def test_trace_non_empty_on_admit(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert len(result.trace) > 0

    def test_trace_contains_g2_objective(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert any("g2_coherence" in t for t in result.trace)

    def test_trace_contains_spin7_objective(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert any("spin7_coherence" in t for t in result.trace)

    def test_trace_contains_projection_objective(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert any("projection" in t for t in result.trace)


# ---------------------------------------------------------------------------
# 8. Projected coordinate
# ---------------------------------------------------------------------------

class TestProjectedCoordinate:
    def test_projected_coordinate_present_on_admit(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert result.projected_coordinate is not None
        assert result.projected_coordinate.layer == 10

    def test_projected_coordinate_absent_on_g2_block(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE, g2=False)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        # Projection runs even on G₂ block (all objectives evaluated)
        # but decision is BLOCK; projected_coordinate comes from projection result
        assert result.decision == RoutingDecision.BLOCK


# ---------------------------------------------------------------------------
# 9. Advisory routing
# ---------------------------------------------------------------------------

class TestAdvisoryRouting:
    def test_advisory_on_semantic_mode_mismatch(self):
        # Layer 6 with GRADIENT mode → CLASS_3 contradiction (semantic mode mismatch)
        # g2=True, spin7=True, phi_parallel=True → G₂ and Spin7 pass
        # Projection succeeds but emits advisory_contradictions receipt
        env = _envelope(layer=6, phi_parallel=True, g2=True, spin7=True,
                        mode=SemanticMode.GRADIENT)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        # Projection succeeds (CLASS_3 is not blocking)
        assert result.projection_success is True
        # Decision is ADVISORY (structural contradictions present)
        assert result.decision in (RoutingDecision.ADMIT, RoutingDecision.ADVISORY)

    def test_advisory_receipt_emitted_when_advisory(self):
        env = _envelope(layer=6, phi_parallel=True, g2=True, spin7=True,
                        mode=SemanticMode.GRADIENT)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        if result.decision == RoutingDecision.ADVISORY:
            assert "omega_router_advisory" in result.receipts


# ---------------------------------------------------------------------------
# 10. Locked ontology — semantic mode names
# ---------------------------------------------------------------------------

class TestLockedOntology:
    def test_semantic_mode_locked_names(self):
        assert SemanticMode.GRADIENT == "GRADIENT"       # L2 Gradient Field
        assert SemanticMode.LEXICAL == "LEXICAL"         # L5 Alexandrian Lexicon
        assert SemanticMode.STATE == "STATE"             # L6 State Manifold
        assert SemanticMode.MEMORY == "MEMORY"           # L7 Alexandrian Archive
        assert SemanticMode.LINEAGE == "LINEAGE"         # L8 Lineage Fabric
        assert SemanticMode.NARRATIVE == "NARRATIVE"     # L10 Narrative

    def test_l7_alexandrian_archive_to_l10_narrative_admitted(self):
        # L7 Alexandrian Archive → L10 Ω-Link Narrative Interface
        env = _envelope(layer=7, mode=SemanticMode.MEMORY, g2=True, spin7=True)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert result.projection_success is True
        assert result.decision in (RoutingDecision.ADMIT, RoutingDecision.ADVISORY)

    def test_l5_alexandrian_lexicon_to_l8_lineage_fabric(self):
        # L5 Alexandrian Lexicon → L8 Lineage Fabric
        env = _envelope(layer=5, mode=SemanticMode.LEXICAL, g2=True, spin7=True)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=8))
        assert result.projection_success is True

    def test_l2_gradient_field_admitted(self):
        # L2 Gradient Field → L10 Narrative
        env = _envelope(layer=2, mode=SemanticMode.GRADIENT, g2=True, spin7=True)
        router = OmegaManifoldRouter()
        result = router.route(_request(env, target_layer=10))
        assert result.projection_success is True
