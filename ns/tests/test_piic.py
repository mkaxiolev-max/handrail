"""PIIC chain tests — monotonic advance + no-skip + gate-on-NCOM (B7).

Tag: piic-chain-v2
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# PIICStage enum
# ---------------------------------------------------------------------------


class TestPIICStageEnum:
    def test_all_four_stages_present(self):
        from ns.services.piic.chain import PIICStage

        names = {s.value for s in PIICStage}
        assert names == {"perception", "interpretation", "identification", "commitment"}

    def test_stages_are_string_enum(self):
        from ns.services.piic.chain import PIICStage

        assert PIICStage.perception == "perception"
        assert PIICStage.commitment == "commitment"

    def test_stage_order_starts_with_perception(self):
        from ns.services.piic.chain import PIICStage, STAGE_ORDER

        assert STAGE_ORDER[0] == PIICStage.perception

    def test_stage_order_ends_with_commitment(self):
        from ns.services.piic.chain import PIICStage, STAGE_ORDER

        assert STAGE_ORDER[-1] == PIICStage.commitment

    def test_stage_order_has_four_elements(self):
        from ns.services.piic.chain import STAGE_ORDER

        assert len(STAGE_ORDER) == 4

    def test_stage_order_is_canonical(self):
        from ns.services.piic.chain import PIICStage, STAGE_ORDER

        assert STAGE_ORDER == [
            PIICStage.perception,
            PIICStage.interpretation,
            PIICStage.identification,
            PIICStage.commitment,
        ]


# ---------------------------------------------------------------------------
# PIICChain — initial state
# ---------------------------------------------------------------------------


class TestPIICChainInit:
    def test_initial_stage_is_perception(self):
        from ns.services.piic.chain import PIICChain, PIICStage

        assert PIICChain().stage == PIICStage.perception

    def test_initial_history_contains_only_perception(self):
        from ns.services.piic.chain import PIICChain, PIICStage

        c = PIICChain()
        assert c.history == [PIICStage.perception]

    def test_is_committed_false_at_start(self):
        from ns.services.piic.chain import PIICChain

        assert PIICChain().is_committed() is False


# ---------------------------------------------------------------------------
# PIICChain — monotonic advance
# ---------------------------------------------------------------------------


class TestPIICChainMonotonicAdvance:
    def test_advance_perception_to_interpretation(self):
        from ns.services.piic.chain import PIICChain, PIICStage

        c = PIICChain()
        result = c.advance()
        assert result == PIICStage.interpretation
        assert c.stage == PIICStage.interpretation

    def test_advance_interpretation_to_identification(self):
        from ns.services.piic.chain import PIICChain, PIICStage

        c = PIICChain()
        c.advance()
        result = c.advance()
        assert result == PIICStage.identification

    def test_advance_identification_to_commitment(self):
        from ns.services.piic.chain import PIICChain, PIICStage

        c = PIICChain()
        c.advance(); c.advance()
        result = c.advance()
        assert result == PIICStage.commitment

    def test_full_chain_advance_sequence(self):
        from ns.services.piic.chain import PIICChain, PIICStage

        c = PIICChain()
        stages = [c.advance() for _ in range(3)]
        assert stages == [
            PIICStage.interpretation,
            PIICStage.identification,
            PIICStage.commitment,
        ]

    def test_is_committed_true_after_full_advance(self):
        from ns.services.piic.chain import PIICChain

        c = PIICChain()
        c.advance(); c.advance(); c.advance()
        assert c.is_committed() is True

    def test_history_tracks_all_stages_after_full_advance(self):
        from ns.services.piic.chain import PIICChain, PIICStage

        c = PIICChain()
        c.advance(); c.advance(); c.advance()
        assert c.history == [
            PIICStage.perception,
            PIICStage.interpretation,
            PIICStage.identification,
            PIICStage.commitment,
        ]

    def test_history_after_two_advances(self):
        from ns.services.piic.chain import PIICChain, PIICStage

        c = PIICChain()
        c.advance(); c.advance()
        assert c.history == [
            PIICStage.perception,
            PIICStage.interpretation,
            PIICStage.identification,
        ]

    def test_history_is_copy_not_reference(self):
        from ns.services.piic.chain import PIICChain

        c = PIICChain()
        h = c.history
        c.advance()
        assert len(h) == 1  # original snapshot unchanged


# ---------------------------------------------------------------------------
# PIICChain — no-skip enforcement (I10 monotone)
# ---------------------------------------------------------------------------


class TestPIICChainNoSkip:
    def test_advance_beyond_commitment_raises(self):
        from ns.services.piic.chain import PIICChain

        c = PIICChain()
        c.advance(); c.advance(); c.advance()
        with pytest.raises(ValueError):
            c.advance()

    def test_advance_to_valid_next_step(self):
        from ns.services.piic.chain import PIICChain, PIICStage

        c = PIICChain()
        c.advance_to(PIICStage.interpretation)
        assert c.stage == PIICStage.interpretation

    def test_advance_to_skip_one_raises(self):
        from ns.services.piic.chain import PIICChain, PIICStage

        c = PIICChain()
        with pytest.raises(ValueError, match="Cannot skip"):
            c.advance_to(PIICStage.identification)

    def test_advance_to_skip_two_raises(self):
        from ns.services.piic.chain import PIICChain, PIICStage

        c = PIICChain()
        with pytest.raises(ValueError, match="Cannot skip"):
            c.advance_to(PIICStage.commitment)

    def test_advance_to_regress_raises(self):
        from ns.services.piic.chain import PIICChain, PIICStage

        c = PIICChain()
        c.advance()
        with pytest.raises(ValueError, match="Cannot regress"):
            c.advance_to(PIICStage.perception)

    def test_advance_to_same_stage_raises(self):
        from ns.services.piic.chain import PIICChain, PIICStage

        c = PIICChain()
        with pytest.raises(ValueError):
            c.advance_to(PIICStage.perception)

    def test_advance_to_regress_from_identification_raises(self):
        from ns.services.piic.chain import PIICChain, PIICStage

        c = PIICChain()
        c.advance(); c.advance()
        with pytest.raises(ValueError, match="Cannot regress"):
            c.advance_to(PIICStage.interpretation)

    def test_advance_to_updates_history(self):
        from ns.services.piic.chain import PIICChain, PIICStage

        c = PIICChain()
        c.advance_to(PIICStage.interpretation)
        c.advance_to(PIICStage.identification)
        assert PIICStage.identification in c.history


# ---------------------------------------------------------------------------
# Gate-on-NCOM — PIIC promotion gate requires NCOM collapse readiness (B4)
# ---------------------------------------------------------------------------


def _piic_gate_context() -> dict:
    """Fully passing context including NCOM/PIIC collapse fields."""
    from ns.services.loom.service import ConfidenceEnvelope
    from ns.services.ncom.readiness import CollapseReadiness
    from ns.services.ncom.state import NCOMState
    from ns.services.piic.chain import PIICStage

    return {
        "confidence": ConfidenceEnvelope(
            evidence=0.9, contradiction=0.1, novelty=0.8, stability=0.9
        ),
        "contradiction_weight": 0.10,
        "reconstructability": 0.95,
        "lineage_valid": True,
        "hic_approval": True,
        "pdp_approval": True,
        "quorum_certs": [{"serial": "26116460"}],
        "state": {"coherent": True},
        "ncom_state": NCOMState.ready_for_collapse,
        "piic_stage": PIICStage.commitment,
        "readiness": CollapseReadiness(
            ERS=0.8,
            CRS=0.8,
            IPI=0.6,
            contradictionPressure=0.2,
            branchDiversityAdequacy=0.7,
        ),
    }


class TestPIICGateOnNCOM:
    def test_gate_passes_with_piic_committed_and_ncom_ready(self):
        from ns.services.canon.promotion_guard import PromotionGuard

        assert PromotionGuard().can_promote("br_piic_01", _piic_gate_context()) is True

    def test_gate_blocked_when_piic_at_perception(self):
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.piic.chain import PIICStage

        ctx = _piic_gate_context()
        ctx["piic_stage"] = PIICStage.perception
        assert PromotionGuard().can_promote("br_piic_01", ctx) is False

    def test_gate_blocked_when_piic_at_interpretation(self):
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.piic.chain import PIICStage

        ctx = _piic_gate_context()
        ctx["piic_stage"] = PIICStage.interpretation
        assert PromotionGuard().can_promote("br_piic_01", ctx) is False

    def test_gate_blocked_when_piic_at_identification(self):
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.piic.chain import PIICStage

        ctx = _piic_gate_context()
        ctx["piic_stage"] = PIICStage.identification
        assert PromotionGuard().can_promote("br_piic_01", ctx) is False

    def test_gate_blocked_when_ncom_not_collapse_ready(self):
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.ncom.state import NCOMState

        ctx = _piic_gate_context()
        ctx["ncom_state"] = NCOMState.stabilizing
        assert PromotionGuard().can_promote("br_piic_01", ctx) is False

    def test_gate_blocked_when_ncom_observing(self):
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.ncom.state import NCOMState

        ctx = _piic_gate_context()
        ctx["ncom_state"] = NCOMState.observing
        assert PromotionGuard().can_promote("br_piic_01", ctx) is False

    def test_gate_passes_with_forced_collapse_state(self):
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.ncom.state import NCOMState

        ctx = _piic_gate_context()
        ctx["ncom_state"] = NCOMState.forced_collapse
        assert PromotionGuard().can_promote("br_piic_01", ctx) is True

    def test_gate_blocked_when_readiness_action_is_wait(self):
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.ncom.readiness import CollapseReadiness

        ctx = _piic_gate_context()
        ctx["readiness"] = CollapseReadiness(ERS=0.1)  # → wait
        assert PromotionGuard().can_promote("br_piic_01", ctx) is False

    def test_gate_blocked_when_hard_vetoes_present(self):
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.ncom.readiness import CollapseReadiness

        ctx = _piic_gate_context()
        ctx["readiness"] = CollapseReadiness(
            ERS=0.8,
            CRS=0.8,
            IPI=0.6,
            contradictionPressure=0.2,
            branchDiversityAdequacy=0.7,
            hardVetoes=["lineage_gap_detected"],
        )
        assert PromotionGuard().can_promote("br_piic_01", ctx) is False

    def test_promote_emits_ncom_veto_receipt_on_ncom_block(self, tmp_path):
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.ncom.state import NCOMState

        ctx = _piic_gate_context()
        ctx["ncom_state"] = NCOMState.branching
        result = PromotionGuard().promote(
            "br_piic_01", ctx, receipt_path=tmp_path / "r.jsonl"
        )
        assert result["receipt_name"] == "ncom_veto_emitted"
        assert result["allowed"] is False

    def test_promote_includes_veto_reason_on_piic_block(self):
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.piic.chain import PIICStage

        ctx = _piic_gate_context()
        ctx["piic_stage"] = PIICStage.identification
        result = PromotionGuard().promote("br_piic_01", ctx)
        assert "veto_reason" in result
        assert "piic_stage_not_commitment" in result["veto_reason"]

    def test_promote_includes_veto_reason_on_ncom_block(self):
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.ncom.state import NCOMState

        ctx = _piic_gate_context()
        ctx["ncom_state"] = NCOMState.priming
        result = PromotionGuard().promote("br_piic_01", ctx)
        assert "veto_reason" in result
        assert "ncom_state_not_collapse_ready" in result["veto_reason"]

    def test_piic_stage_as_string_accepted(self):
        from ns.services.canon.promotion_guard import PromotionGuard

        ctx = _piic_gate_context()
        ctx["piic_stage"] = "commitment"
        assert PromotionGuard().can_promote("br_piic_01", ctx) is True

    def test_ncom_state_as_string_accepted(self):
        from ns.services.canon.promotion_guard import PromotionGuard

        ctx = _piic_gate_context()
        ctx["ncom_state"] = "ready_for_collapse"
        assert PromotionGuard().can_promote("br_piic_01", ctx) is True

    def test_piic_chain_to_gate_integration(self):
        """Drive a real PIICChain to commitment then verify promotion gate passes."""
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.piic.chain import PIICChain

        chain = PIICChain()
        chain.advance(); chain.advance(); chain.advance()
        assert chain.is_committed()

        ctx = _piic_gate_context()
        ctx["piic_stage"] = chain.stage
        assert PromotionGuard().can_promote("br_piic_integration", ctx) is True

    def test_gate_blocked_when_piic_chain_not_yet_committed(self):
        """Drive a PIICChain only partway; gate must block."""
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.piic.chain import PIICChain

        chain = PIICChain()
        chain.advance()  # → interpretation only

        ctx = _piic_gate_context()
        ctx["piic_stage"] = chain.stage
        assert PromotionGuard().can_promote("br_piic_partial", ctx) is False


# ---------------------------------------------------------------------------
# Receipt names for PIIC
# ---------------------------------------------------------------------------


class TestPIICReceiptNames:
    def test_piic_stage_advanced_in_registry(self):
        from ns.domain.receipts.names import RECEIPT_NAMES

        assert "piic_stage_advanced" in RECEIPT_NAMES

    def test_ncom_veto_emitted_in_registry(self):
        from ns.domain.receipts.names import RECEIPT_NAMES

        assert "ncom_veto_emitted" in RECEIPT_NAMES

    def test_ncom_state_transitioned_in_registry(self):
        from ns.domain.receipts.names import RECEIPT_NAMES

        assert "ncom_state_transitioned" in RECEIPT_NAMES
