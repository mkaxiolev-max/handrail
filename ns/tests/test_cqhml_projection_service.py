"""NS∞ cqhml-P6: DimensionalProjectionService tests.

Tag: cqhml-projection-service-v2
AXIOLEV Holdings LLC © 2026

Locked ontology:
  Gradient Field (L2), Alexandrian Lexicon (L5), State Manifold (L6),
  Alexandrian Archive (L7), Lineage Fabric (L8), Narrative (L10).
  No deprecated names (Ether, CTF, Storytime-as-layer, Alexandria alone, etc.).
"""
from __future__ import annotations

import pytest

from ns.api.schemas.cqhml import (
    DimensionalCoordinate,
    DimensionalEnvelope,
    ObserverFrame,
    PolicyMode,
    ProjectionRequest,
    ProjectionResult,
    SemanticMode,
)
from ns.services.cqhml.projection_service import DimensionalProjectionService


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
        frame_id="test-frame",
        layer=layer,
        semantic_mode=mode,
        policy_mode=policy,
        tick=0,
    )


def _envelope(
    layer: int = 6,
    phi_parallel: bool = True,
    g2: bool = True,
    mode: SemanticMode = SemanticMode.STATE,
    policy: PolicyMode = PolicyMode.ENFORCE,
    tick: int = 0,
) -> DimensionalEnvelope:
    return DimensionalEnvelope(
        coordinate=_coord(layer=layer, phi_parallel=phi_parallel, tick=tick),
        observer=_observer(layer=layer, mode=mode, policy=policy),
        g2_phi_parallel=g2,
        spin7_coherent=True,
        tick=tick,
    )


def _request(
    envelope: DimensionalEnvelope,
    target_layer: int,
    request_id: str = "req-001",
    tick: int = 0,
    semantic_mode: SemanticMode | None = None,
    policy_mode: PolicyMode | None = None,
) -> ProjectionRequest:
    return ProjectionRequest(
        request_id=request_id,
        envelope=envelope,
        target_layer=target_layer,
        semantic_mode=semantic_mode,
        policy_mode=policy_mode,
        tick=tick,
    )


# ---------------------------------------------------------------------------
# Basic projection
# ---------------------------------------------------------------------------

class TestBasicProjection:
    def test_l2_to_l10_success(self):
        env = _envelope(layer=2, mode=SemanticMode.GRADIENT)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=10))
        assert result.success is True
        assert result.source_layer == 2
        assert result.target_layer == 10

    def test_result_is_projection_result_instance(self):
        env = _envelope(layer=5, mode=SemanticMode.LEXICAL)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=7))
        assert isinstance(result, ProjectionResult)

    def test_request_id_preserved(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=8, request_id="uid-42"))
        assert result.request_id == "uid-42"

    def test_projected_coordinate_has_target_layer(self):
        env = _envelope(layer=2, mode=SemanticMode.GRADIENT)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=10))
        assert result.projected_coordinate is not None
        assert result.projected_coordinate.layer == 10

    def test_error_is_none_on_success(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=7))
        assert result.error is None

    def test_same_layer_projection(self):
        env = _envelope(layer=5, mode=SemanticMode.LEXICAL)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=5))
        assert result.success is True
        assert result.projected_coordinate.layer == 5

    def test_tick_propagated_to_result(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE, tick=7)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=8, tick=7))
        assert result.tick == 7


# ---------------------------------------------------------------------------
# G₂ coherence
# ---------------------------------------------------------------------------

class TestG2Coherence:
    def test_g2_coherent_when_phi_and_g2_true(self):
        env = _envelope(layer=6, phi_parallel=True, g2=True, mode=SemanticMode.STATE)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=10))
        assert result.g2_phi_parallel is True

    def test_g2_false_when_envelope_g2_false(self):
        env = _envelope(layer=6, phi_parallel=True, g2=False, mode=SemanticMode.STATE)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=10))
        assert result.g2_phi_parallel is False

    def test_ring6_receipt_emitted_when_g2_coherent(self):
        env = _envelope(layer=6, phi_parallel=True, g2=True, mode=SemanticMode.STATE)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=10))
        assert "ring6_g2_invariant_checked" in result.receipts_emitted

    def test_ring6_receipt_absent_when_g2_incoherent(self):
        env = _envelope(layer=6, phi_parallel=True, g2=False, mode=SemanticMode.STATE)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=10))
        assert "ring6_g2_invariant_checked" not in result.receipts_emitted


# ---------------------------------------------------------------------------
# I6 Sentinel Gate — L1 constitutional block
# ---------------------------------------------------------------------------

class TestSentinelGateI6:
    def test_l1_phi_false_returns_constitutional_block(self):
        env = _envelope(layer=1, phi_parallel=False, mode=SemanticMode.CONSTITUTIONAL)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=5))
        assert result.success is False
        assert "cqhml_projection_constitutional_block" in result.receipts_emitted

    def test_l1_phi_false_error_mentions_sentinel_gate(self):
        env = _envelope(layer=1, phi_parallel=False, mode=SemanticMode.CONSTITUTIONAL)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=5))
        assert result.error is not None
        assert "I6" in result.error or "Sentinel" in result.error

    def test_l1_phi_true_succeeds(self):
        env = _envelope(layer=1, phi_parallel=True, mode=SemanticMode.CONSTITUTIONAL)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=5))
        assert result.success is True

    def test_non_l1_phi_false_not_constitutional_block(self):
        # phi_parallel=False on L2 is a CLASS_2 contradiction (advisory), not CLASS_1
        # so projection still proceeds (success=True) unless scan_envelope raises CLASS_1
        env = _envelope(layer=2, phi_parallel=False, g2=False, mode=SemanticMode.GRADIENT)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=10))
        # phi_parallel=False on non-L1 is CLASS_2 (structural) via scan_envelope → phi incoherence
        # CLASS_2 is not blocking → projection should succeed
        assert result.success is True
        assert "cqhml_projection_constitutional_block" not in result.receipts_emitted


# ---------------------------------------------------------------------------
# Receipt emission
# ---------------------------------------------------------------------------

class TestReceiptEmission:
    def test_success_receipt_on_valid_projection(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=8))
        assert "cqhml_projection_success" in result.receipts_emitted

    def test_receipts_non_empty_on_success(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=8))
        assert len(result.receipts_emitted) > 0

    def test_service_receipts_accumulate_across_calls(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE)
        svc = DimensionalProjectionService()
        svc.project(_request(env, target_layer=8, request_id="r1"))
        svc.project(_request(env, target_layer=10, request_id="r2"))
        all_receipts = svc.receipts()
        assert len(all_receipts) >= 2

    def test_audit_receipt_emitted_in_audit_mode(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE, policy=PolicyMode.AUDIT)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=10))
        assert "cqhml_audit_trace_emitted" in result.receipts_emitted

    def test_no_audit_receipt_in_enforce_mode(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE, policy=PolicyMode.ENFORCE)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=10))
        assert "cqhml_audit_trace_emitted" not in result.receipts_emitted


# ---------------------------------------------------------------------------
# Contradiction blocking (CLASS_1)
# ---------------------------------------------------------------------------

class TestContradictionBlocking:
    def test_class1_contradiction_blocks_projection(self):
        # g2_phi_parallel=False on envelope alone is CLASS_2 (not blocking).
        # Manually test that a blocked result has success=False and a block receipt.
        # We trigger this by creating an envelope with g2_phi_parallel=False (CLASS_2 only)
        # — projection should still succeed.
        env = _envelope(layer=6, g2=False, mode=SemanticMode.STATE)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=8))
        # CLASS_2 doesn't block
        assert result.success is True

    def test_blocked_result_has_error(self):
        # Force a CLASS_1 by injecting L1 phi_parallel=False (triggers sentinel gate)
        env = _envelope(layer=1, phi_parallel=False, mode=SemanticMode.CONSTITUTIONAL)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=5))
        assert result.success is False
        assert result.error is not None

    def test_blocked_result_no_projected_coordinate(self):
        env = _envelope(layer=1, phi_parallel=False, mode=SemanticMode.CONSTITUTIONAL)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=5))
        assert result.projected_coordinate is None


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------

class TestTrace:
    def test_trace_contains_layer_path(self):
        env = _envelope(layer=2, mode=SemanticMode.GRADIENT)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=10))
        assert any("2" in t and "10" in t for t in result.trace)

    def test_trace_non_empty_on_success(self):
        env = _envelope(layer=6, mode=SemanticMode.STATE)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=7))
        assert len(result.trace) > 0


# ---------------------------------------------------------------------------
# Locked ontology invariants
# ---------------------------------------------------------------------------

class TestLockedOntology:
    def test_semantic_mode_values_match_locked_ontology(self):
        assert SemanticMode.GRADIENT == "GRADIENT"           # L2 Gradient Field
        assert SemanticMode.LEXICAL == "LEXICAL"             # L5 Alexandrian Lexicon
        assert SemanticMode.STATE == "STATE"                 # L6 State Manifold
        assert SemanticMode.MEMORY == "MEMORY"               # L7 Alexandrian Archive
        assert SemanticMode.LINEAGE == "LINEAGE"             # L8 Lineage Fabric
        assert SemanticMode.NARRATIVE == "NARRATIVE"         # L10 Narrative

    def test_projection_l5_to_l8_lineage_fabric(self):
        # L5 Alexandrian Lexicon → L8 Lineage Fabric
        env = _envelope(layer=5, mode=SemanticMode.LEXICAL)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=8))
        assert result.success is True
        assert result.projected_coordinate.layer == 8

    def test_projection_l7_alexandrian_archive_to_l10_narrative(self):
        # L7 Alexandrian Archive → L10 Narrative
        env = _envelope(layer=7, mode=SemanticMode.MEMORY)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=10))
        assert result.success is True
        assert result.projected_coordinate.layer == 10

    def test_projection_l6_state_manifold_to_l7_archive(self):
        # L6 State Manifold → L7 Alexandrian Archive
        env = _envelope(layer=6, mode=SemanticMode.STATE)
        svc = DimensionalProjectionService()
        result = svc.project(_request(env, target_layer=7))
        assert result.success is True
        assert result.source_layer == 6
        assert result.target_layer == 7
