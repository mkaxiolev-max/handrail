"""NS∞ cqhml-P9: OracleDimensionalGate tests — CQHML Ω-router × Oracle v2.

Validates ns/services/oracle/dimensional_gate.py:
  * DimensionalGateResult dataclass
  * OracleDimensionalGate.evaluate() — full pipeline
  * Routing decision → oracle decision mapping
    ADMIT → ALLOW, ADVISORY → DEFER, BLOCK → DENY
  * G₂ and Spin(7) gate propagation into oracle layer
  * Receipt emission (I2 append-only, I10 snapshot isolation)
  * Invariants I1, I2, I5, I6, I7, I10

Locked ontology enforced: Gradient Field (L2), Alexandrian Lexicon (L5),
State Manifold (L6), Alexandrian Archive (L7), Lineage Fabric (L8), Narrative (L10).
No deprecated names (Ether, CTF, Storytime-as-layer, Alexandria alone, etc.).

Tag: cqhml-oracle-dim-gate-v2
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
from ns.api.schemas.oracle import (
    HandrailExecutionEnvelope,
    OracleDecision,
    OracleSeverity,
)
from ns.services.omega.manifold_router import RoutingDecision
from ns.services.oracle.dimensional_gate import (
    DimensionalGateResult,
    OracleDimensionalGate,
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
        frame_id="test-dim-gate-frame",
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
    request_id: str = "dim-gate-req-001",
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


def _admit_request(
    request_id: str = "dim-gate-admit-001",
    tick: int = 0,
    target_layer: int = 10,
) -> ProjectionRequest:
    return _request(
        _envelope(layer=6, mode=SemanticMode.STATE, g2=True, spin7=True),
        target_layer=target_layer,
        request_id=request_id,
        tick=tick,
    )


def _block_g2_request(request_id: str = "dim-gate-block-g2") -> ProjectionRequest:
    return _request(
        _envelope(layer=6, mode=SemanticMode.STATE, g2=False),
        target_layer=10,
        request_id=request_id,
    )


def _block_spin7_request(request_id: str = "dim-gate-block-s7") -> ProjectionRequest:
    return _request(
        _envelope(layer=6, mode=SemanticMode.STATE, g2=True, spin7=False),
        target_layer=10,
        request_id=request_id,
    )


# ---------------------------------------------------------------------------
# 1. Module surface
# ---------------------------------------------------------------------------

class TestModuleSurface:
    def test_importable_symbols(self):
        import ns.services.oracle.dimensional_gate as m
        for name in ("DimensionalGateResult", "OracleDimensionalGate"):
            assert hasattr(m, name), f"Missing symbol: {name}"

    def test_oracle_dimensional_gate_instantiable(self):
        gate = OracleDimensionalGate()
        assert gate is not None

    def test_dimensional_gate_result_is_dataclass(self):
        from dataclasses import fields
        field_names = {f.name for f in fields(DimensionalGateResult)}
        for required in (
            "request_id", "routing_decision", "oracle_decision", "oracle_severity",
            "g2_phi_parallel", "spin7_phi_parallel", "projection_success",
            "receipts", "trace", "tick", "error", "projected_coordinate",
        ):
            assert required in field_names, f"Missing field: {required}"

    def test_routing_decision_imported(self):
        assert RoutingDecision.ADMIT == "ADMIT"
        assert RoutingDecision.ADVISORY == "ADVISORY"
        assert RoutingDecision.BLOCK == "BLOCK"

    def test_oracle_decision_imported(self):
        assert OracleDecision.ALLOW == "ALLOW"
        assert OracleDecision.DEFER == "DEFER"
        assert OracleDecision.DENY == "DENY"


# ---------------------------------------------------------------------------
# 2. Basic ALLOW gate (fully coherent envelope)
# ---------------------------------------------------------------------------

class TestAllowGate:
    def test_evaluate_returns_dimensional_gate_result(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_admit_request())
        assert isinstance(result, DimensionalGateResult)

    def test_admit_routing_yields_allow_oracle(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_admit_request())
        assert result.routing_decision == RoutingDecision.ADMIT
        assert result.oracle_decision == OracleDecision.ALLOW

    def test_allow_severity_is_nominal(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_admit_request())
        assert result.oracle_severity == OracleSeverity.NOMINAL

    def test_request_id_preserved(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_admit_request(request_id="uid-dim-999"))
        assert result.request_id == "uid-dim-999"

    def test_tick_propagated(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_admit_request(tick=42))
        assert result.tick == 42

    def test_g2_flag_true_on_allow(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_admit_request())
        assert result.g2_phi_parallel is True

    def test_spin7_flag_true_on_allow(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_admit_request())
        assert result.spin7_phi_parallel is True

    def test_projection_success_true_on_allow(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_admit_request())
        assert result.projection_success is True

    def test_projected_coordinate_present_on_allow(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_admit_request(target_layer=10))
        assert result.projected_coordinate is not None
        assert result.projected_coordinate.layer == 10

    def test_no_error_on_allow(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_admit_request())
        assert result.error is None


# ---------------------------------------------------------------------------
# 3. G₂ block → DENY (I6 Sentinel Gate)
# ---------------------------------------------------------------------------

class TestG2BlockDeny:
    def test_g2_false_routing_block(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_block_g2_request())
        assert result.routing_decision == RoutingDecision.BLOCK

    def test_g2_false_oracle_deny(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_block_g2_request())
        assert result.oracle_decision == OracleDecision.DENY

    def test_g2_block_severity_critical_or_higher(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_block_g2_request())
        assert result.oracle_severity in (OracleSeverity.CRITICAL, OracleSeverity.CONSTITUTIONAL)

    def test_g2_flag_false_in_result(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_block_g2_request())
        assert result.g2_phi_parallel is False

    def test_g2_block_has_error(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_block_g2_request())
        assert result.error is not None
        assert "G₂" in result.error or "g2" in result.error.lower() or "I6" in result.error

    def test_g2_block_dim_gate_block_receipt(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_block_g2_request())
        assert "dim_gate_block" in result.receipts


# ---------------------------------------------------------------------------
# 4. Spin(7) block → DENY
# ---------------------------------------------------------------------------

class TestSpin7BlockDeny:
    def test_spin7_false_routing_block(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_block_spin7_request())
        assert result.routing_decision == RoutingDecision.BLOCK

    def test_spin7_false_oracle_deny(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_block_spin7_request())
        assert result.oracle_decision == OracleDecision.DENY

    def test_spin7_flag_false_in_result(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_block_spin7_request())
        assert result.spin7_phi_parallel is False

    def test_spin7_block_dim_gate_receipt(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_block_spin7_request())
        assert "dim_gate_block" in result.receipts


# ---------------------------------------------------------------------------
# 5. Advisory → DEFER
# ---------------------------------------------------------------------------

class TestAdvisoryDefer:
    def test_advisory_routing_yields_defer_or_allow(self):
        # L6 with GRADIENT mode → advisory contradiction → ADVISORY routing
        env = _envelope(layer=6, phi_parallel=True, g2=True, spin7=True,
                        mode=SemanticMode.GRADIENT)
        req = _request(env, target_layer=10, request_id="dim-gate-advisory-001")
        gate = OracleDimensionalGate()
        result = gate.evaluate(req)
        # ADVISORY routing → WARN RIL effect → DEFER oracle (or ADMIT→ALLOW)
        assert result.routing_decision in (RoutingDecision.ADVISORY, RoutingDecision.ADMIT)
        if result.routing_decision == RoutingDecision.ADVISORY:
            assert result.oracle_decision == OracleDecision.DEFER

    def test_advisory_oracle_severity_advisory_or_nominal(self):
        env = _envelope(layer=6, phi_parallel=True, g2=True, spin7=True,
                        mode=SemanticMode.GRADIENT)
        req = _request(env, target_layer=10, request_id="dim-gate-advisory-002")
        gate = OracleDimensionalGate()
        result = gate.evaluate(req)
        assert result.oracle_severity in (OracleSeverity.ADVISORY, OracleSeverity.NOMINAL)

    def test_advisory_projection_succeeds(self):
        env = _envelope(layer=6, phi_parallel=True, g2=True, spin7=True,
                        mode=SemanticMode.GRADIENT)
        req = _request(env, target_layer=10, request_id="dim-gate-advisory-003")
        gate = OracleDimensionalGate()
        result = gate.evaluate(req)
        assert result.projection_success is True


# ---------------------------------------------------------------------------
# 6. L1 constitutional projection block → DENY
# ---------------------------------------------------------------------------

class TestConstitutionalProjectionBlock:
    def test_l1_phi_false_routing_block(self):
        env = _envelope(
            layer=1, phi_parallel=False, mode=SemanticMode.CONSTITUTIONAL,
            g2=True, spin7=True,
        )
        req = _request(env, target_layer=5, request_id="dim-gate-l1-block")
        gate = OracleDimensionalGate()
        result = gate.evaluate(req)
        assert result.routing_decision == RoutingDecision.BLOCK

    def test_l1_phi_false_oracle_deny(self):
        env = _envelope(
            layer=1, phi_parallel=False, mode=SemanticMode.CONSTITUTIONAL,
            g2=True, spin7=True,
        )
        req = _request(env, target_layer=5, request_id="dim-gate-l1-deny")
        gate = OracleDimensionalGate()
        result = gate.evaluate(req)
        assert result.oracle_decision == OracleDecision.DENY


# ---------------------------------------------------------------------------
# 7. Receipt emission
# ---------------------------------------------------------------------------

class TestReceiptEmission:
    def test_allow_dim_gate_pass_receipt(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_admit_request(request_id="dim-gate-r1"))
        assert "dim_gate_pass" in result.receipts

    def test_block_dim_gate_block_receipt(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_block_g2_request(request_id="dim-gate-r2"))
        assert "dim_gate_block" in result.receipts

    def test_receipts_non_empty_on_allow(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_admit_request(request_id="dim-gate-r3"))
        assert len(result.receipts) > 0

    def test_oracle_decision_receipt_present(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_admit_request(request_id="dim-gate-r4"))
        assert any("dim_gate_oracle_decision_" in r for r in result.receipts)

    def test_omega_router_receipt_propagated(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_admit_request(request_id="dim-gate-r5"))
        # OmegaRouter emits omega_router_admit or omega_router_g2_coherence_pass
        assert any("omega_router" in r for r in result.receipts)

    def test_g2_coherence_receipt_propagated(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_admit_request(request_id="dim-gate-r6"))
        assert "omega_router_g2_coherence_pass" in result.receipts

    def test_receipts_accumulate_across_calls_i2(self):
        gate = OracleDimensionalGate()
        gate.evaluate(_admit_request(request_id="dim-gate-acc-1"))
        gate.evaluate(_admit_request(request_id="dim-gate-acc-2"))
        all_r = gate.receipts()
        assert len(all_r) >= 4

    def test_receipts_snapshot_is_copy_i10(self):
        gate = OracleDimensionalGate()
        gate.evaluate(_admit_request(request_id="dim-gate-copy-1"))
        snap1 = gate.receipts()
        snap1.clear()
        snap2 = gate.receipts()
        assert len(snap2) > 0


# ---------------------------------------------------------------------------
# 8. Trace
# ---------------------------------------------------------------------------

class TestTrace:
    def test_trace_non_empty_on_allow(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_admit_request())
        assert len(result.trace) > 0

    def test_trace_contains_routing_decision(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_admit_request())
        assert any("routing_decision" in t for t in result.trace)

    def test_trace_contains_oracle_severity(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_admit_request())
        assert any("oracle_severity" in t for t in result.trace)

    def test_trace_contains_projection_info(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_admit_request())
        assert any("projection" in t or "layer" in t for t in result.trace)


# ---------------------------------------------------------------------------
# 9. Adjudication response propagation
# ---------------------------------------------------------------------------

class TestAdjudicationResponse:
    def test_adjudication_response_present(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_admit_request())
        assert result.adjudication_response is not None

    def test_routing_result_present(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_admit_request())
        assert result.routing_result is not None

    def test_adjudication_request_id_matches(self):
        gate = OracleDimensionalGate()
        result = gate.evaluate(_admit_request(request_id="dim-gate-adj-001"))
        assert result.adjudication_response.request_id == "dim-gate-adj-001"

    def test_custom_handrail_envelope_accepted(self):
        gate = OracleDimensionalGate()
        he = HandrailExecutionEnvelope(scope="SOVEREIGN", risk_tier="R1", yubikey_verified=True)
        result = gate.evaluate(_admit_request(), handrail_envelope=he)
        assert isinstance(result, DimensionalGateResult)


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

    def test_l7_alexandrian_archive_to_l10_narrative_allowed(self):
        env = _envelope(layer=7, mode=SemanticMode.MEMORY, g2=True, spin7=True)
        req = _request(env, target_layer=10, request_id="dim-gate-l7-l10")
        gate = OracleDimensionalGate()
        result = gate.evaluate(req)
        assert result.oracle_decision in (OracleDecision.ALLOW, OracleDecision.DEFER)

    def test_l2_gradient_field_to_l10_narrative_allowed(self):
        env = _envelope(layer=2, mode=SemanticMode.GRADIENT, g2=True, spin7=True)
        req = _request(env, target_layer=10, request_id="dim-gate-l2-l10")
        gate = OracleDimensionalGate()
        result = gate.evaluate(req)
        assert result.oracle_decision in (OracleDecision.ALLOW, OracleDecision.DEFER)

    def test_l5_alexandrian_lexicon_allowed(self):
        env = _envelope(layer=5, mode=SemanticMode.LEXICAL, g2=True, spin7=True)
        req = _request(env, target_layer=8, request_id="dim-gate-l5-l8")
        gate = OracleDimensionalGate()
        result = gate.evaluate(req)
        assert result.oracle_decision in (OracleDecision.ALLOW, OracleDecision.DEFER)

    def test_l8_lineage_fabric_allowed(self):
        env = _envelope(layer=8, mode=SemanticMode.LINEAGE, g2=True, spin7=True)
        req = _request(env, target_layer=10, request_id="dim-gate-l8-l10")
        gate = OracleDimensionalGate()
        result = gate.evaluate(req)
        assert result.oracle_decision in (OracleDecision.ALLOW, OracleDecision.DEFER)
