"""NCOM runtime tests — 8-state machine + readiness vetoes + collapse gate (B7).

Tag: ncom-piic-tests-green-v2
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# NCOMState enum
# ---------------------------------------------------------------------------


class TestNCOMStateEnum:
    def test_all_eight_states_present(self):
        from ns.services.ncom.state import NCOMState

        names = {s.value for s in NCOMState}
        assert names == {
            "inactive",
            "priming",
            "observing",
            "branching",
            "stabilizing",
            "ready_for_collapse",
            "forced_collapse",
            "aborted",
        }

    def test_state_is_string_enum(self):
        from ns.services.ncom.state import NCOMState

        assert NCOMState.inactive == "inactive"
        assert NCOMState.ready_for_collapse == "ready_for_collapse"

    def test_terminal_states_constant(self):
        from ns.services.ncom.state import NCOMState, TERMINAL_STATES

        assert NCOMState.forced_collapse in TERMINAL_STATES
        assert NCOMState.aborted in TERMINAL_STATES
        assert NCOMState.inactive not in TERMINAL_STATES

    def test_collapse_ready_states_constant(self):
        from ns.services.ncom.state import NCOMState, COLLAPSE_READY_STATES

        assert NCOMState.ready_for_collapse in COLLAPSE_READY_STATES
        assert NCOMState.forced_collapse in COLLAPSE_READY_STATES
        assert NCOMState.stabilizing not in COLLAPSE_READY_STATES


# ---------------------------------------------------------------------------
# NCOMStateMachine — forward transitions
# ---------------------------------------------------------------------------


class TestNCOMStateMachineTransitions:
    def test_initial_state_is_inactive(self):
        from ns.services.ncom.state import NCOMState, NCOMStateMachine

        sm = NCOMStateMachine()
        assert sm.state == NCOMState.inactive

    def test_inactive_to_priming(self):
        from ns.services.ncom.state import NCOMState, NCOMStateMachine

        sm = NCOMStateMachine()
        sm.transition(NCOMState.priming)
        assert sm.state == NCOMState.priming

    def test_full_happy_path(self):
        from ns.services.ncom.state import NCOMState, NCOMStateMachine

        sm = NCOMStateMachine()
        path = [
            NCOMState.priming,
            NCOMState.observing,
            NCOMState.branching,
            NCOMState.stabilizing,
            NCOMState.ready_for_collapse,
            NCOMState.forced_collapse,
        ]
        for target in path:
            sm.transition(target)
        assert sm.state == NCOMState.forced_collapse

    def test_any_non_terminal_can_abort(self):
        from ns.services.ncom.state import NCOMState, NCOMStateMachine

        for start in [
            NCOMState.inactive,
            NCOMState.priming,
            NCOMState.observing,
            NCOMState.branching,
            NCOMState.stabilizing,
            NCOMState.ready_for_collapse,
        ]:
            sm = NCOMStateMachine()
            sm.state = start
            sm._history = [start]
            sm.transition(NCOMState.aborted)
            assert sm.state == NCOMState.aborted

    def test_history_tracks_states(self):
        from ns.services.ncom.state import NCOMState, NCOMStateMachine

        sm = NCOMStateMachine()
        sm.transition(NCOMState.priming)
        sm.transition(NCOMState.observing)
        assert sm.history == [NCOMState.inactive, NCOMState.priming, NCOMState.observing]

    def test_transition_returns_new_state(self):
        from ns.services.ncom.state import NCOMState, NCOMStateMachine

        sm = NCOMStateMachine()
        result = sm.transition(NCOMState.priming)
        assert result == NCOMState.priming


# ---------------------------------------------------------------------------
# NCOMStateMachine — invalid transitions
# ---------------------------------------------------------------------------


class TestNCOMStateMachineInvalidTransitions:
    def test_backward_transition_raises(self):
        from ns.services.ncom.state import NCOMState, NCOMStateMachine

        sm = NCOMStateMachine()
        sm.transition(NCOMState.priming)
        sm.transition(NCOMState.observing)
        with pytest.raises(ValueError, match="Invalid NCOM transition"):
            sm.transition(NCOMState.priming)

    def test_skip_transition_raises(self):
        from ns.services.ncom.state import NCOMState, NCOMStateMachine

        sm = NCOMStateMachine()
        with pytest.raises(ValueError, match="Invalid NCOM transition"):
            sm.transition(NCOMState.observing)

    def test_transition_from_forced_collapse_raises(self):
        from ns.services.ncom.state import NCOMState, NCOMStateMachine

        sm = NCOMStateMachine()
        sm.state = NCOMState.forced_collapse
        with pytest.raises(ValueError):
            sm.transition(NCOMState.aborted)

    def test_transition_from_aborted_raises(self):
        from ns.services.ncom.state import NCOMState, NCOMStateMachine

        sm = NCOMStateMachine()
        sm.state = NCOMState.aborted
        with pytest.raises(ValueError):
            sm.transition(NCOMState.priming)

    def test_is_terminal_true_for_terminal_states(self):
        from ns.services.ncom.state import NCOMState, NCOMStateMachine

        sm = NCOMStateMachine()
        sm.state = NCOMState.forced_collapse
        assert sm.is_terminal() is True

        sm2 = NCOMStateMachine()
        sm2.state = NCOMState.aborted
        assert sm2.is_terminal() is True

    def test_is_terminal_false_for_non_terminal(self):
        from ns.services.ncom.state import NCOMState, NCOMStateMachine

        sm = NCOMStateMachine()
        assert sm.is_terminal() is False

    def test_is_collapse_ready_true(self):
        from ns.services.ncom.state import NCOMState, NCOMStateMachine

        for s in [NCOMState.ready_for_collapse, NCOMState.forced_collapse]:
            sm = NCOMStateMachine()
            sm.state = s
            assert sm.is_collapse_ready() is True

    def test_is_collapse_ready_false_for_other_states(self):
        from ns.services.ncom.state import NCOMState, NCOMStateMachine

        for s in [NCOMState.inactive, NCOMState.priming, NCOMState.stabilizing]:
            sm = NCOMStateMachine()
            sm.state = s
            assert sm.is_collapse_ready() is False


# ---------------------------------------------------------------------------
# CollapseReadiness
# ---------------------------------------------------------------------------


class TestCollapseReadiness:
    def test_default_action_is_wait(self):
        from ns.services.ncom.readiness import CollapseReadiness

        r = CollapseReadiness()
        assert r.recommendedAction == "wait"

    def test_collapse_action_when_all_thresholds_met(self):
        from ns.services.ncom.readiness import CollapseReadiness

        r = CollapseReadiness(
            ERS=0.8,
            CRS=0.8,
            IPI=0.6,
            contradictionPressure=0.2,
            branchDiversityAdequacy=0.7,
        )
        assert r.recommendedAction == "collapse"

    def test_veto_action_when_hard_vetoes_present(self):
        from ns.services.ncom.readiness import CollapseReadiness

        r = CollapseReadiness(
            ERS=0.9,
            CRS=0.9,
            IPI=0.9,
            contradictionPressure=0.0,
            branchDiversityAdequacy=0.9,
            hardVetoes=["lineage_gap_detected"],
        )
        assert r.recommendedAction == "veto"

    def test_veto_takes_precedence_over_collapse_thresholds(self):
        from ns.services.ncom.readiness import CollapseReadiness

        r = CollapseReadiness(
            ERS=1.0, CRS=1.0, IPI=1.0,
            contradictionPressure=0.0, branchDiversityAdequacy=1.0,
            hardVetoes=["unauthorized_branch"],
        )
        assert r.recommendedAction == "veto"

    def test_wait_when_ers_below_threshold(self):
        from ns.services.ncom.readiness import CollapseReadiness

        r = CollapseReadiness(ERS=0.5, CRS=0.8, IPI=0.6, contradictionPressure=0.2, branchDiversityAdequacy=0.7)
        assert r.recommendedAction == "wait"

    def test_wait_when_contradiction_pressure_high(self):
        from ns.services.ncom.readiness import CollapseReadiness

        r = CollapseReadiness(ERS=0.8, CRS=0.8, IPI=0.6, contradictionPressure=0.5, branchDiversityAdequacy=0.7)
        assert r.recommendedAction == "wait"

    def test_hard_vetoes_default_empty(self):
        from ns.services.ncom.readiness import CollapseReadiness

        r = CollapseReadiness()
        assert r.hardVetoes == []

    def test_multiple_vetoes_all_stored(self):
        from ns.services.ncom.readiness import CollapseReadiness

        vetoes = ["lineage_gap", "quorum_missing", "entropy_exceeded"]
        r = CollapseReadiness(hardVetoes=vetoes)
        assert len(r.hardVetoes) == 3


# ---------------------------------------------------------------------------
# PIICStage enum
# ---------------------------------------------------------------------------


class TestPIICStage:
    def test_all_four_stages_present(self):
        from ns.services.piic.chain import PIICStage

        names = {s.value for s in PIICStage}
        assert names == {"perception", "interpretation", "identification", "commitment"}

    def test_stage_order_constant(self):
        from ns.services.piic.chain import PIICStage, STAGE_ORDER

        assert STAGE_ORDER[0] == PIICStage.perception
        assert STAGE_ORDER[-1] == PIICStage.commitment
        assert len(STAGE_ORDER) == 4


# ---------------------------------------------------------------------------
# PIICChain — monotonic progression
# ---------------------------------------------------------------------------


class TestPIICChain:
    def test_initial_stage_is_perception(self):
        from ns.services.piic.chain import PIICChain, PIICStage

        c = PIICChain()
        assert c.stage == PIICStage.perception

    def test_advance_moves_one_step(self):
        from ns.services.piic.chain import PIICChain, PIICStage

        c = PIICChain()
        assert c.advance() == PIICStage.interpretation
        assert c.advance() == PIICStage.identification
        assert c.advance() == PIICStage.commitment

    def test_advance_beyond_commitment_raises(self):
        from ns.services.piic.chain import PIICChain

        c = PIICChain()
        c.advance(); c.advance(); c.advance()
        with pytest.raises(ValueError):
            c.advance()

    def test_advance_to_valid_next_stage(self):
        from ns.services.piic.chain import PIICChain, PIICStage

        c = PIICChain()
        c.advance_to(PIICStage.interpretation)
        assert c.stage == PIICStage.interpretation

    def test_advance_to_skip_raises(self):
        from ns.services.piic.chain import PIICChain, PIICStage

        c = PIICChain()
        with pytest.raises(ValueError, match="Cannot skip"):
            c.advance_to(PIICStage.identification)

    def test_advance_to_regress_raises(self):
        from ns.services.piic.chain import PIICChain, PIICStage

        c = PIICChain()
        c.advance()
        with pytest.raises(ValueError, match="Cannot regress"):
            c.advance_to(PIICStage.perception)

    def test_is_committed_true_at_commitment(self):
        from ns.services.piic.chain import PIICChain

        c = PIICChain()
        c.advance(); c.advance(); c.advance()
        assert c.is_committed() is True

    def test_is_committed_false_initially(self):
        from ns.services.piic.chain import PIICChain

        assert PIICChain().is_committed() is False

    def test_history_tracks_all_stages(self):
        from ns.services.piic.chain import PIICChain, PIICStage

        c = PIICChain()
        c.advance(); c.advance()
        assert c.history == [PIICStage.perception, PIICStage.interpretation, PIICStage.identification]


# ---------------------------------------------------------------------------
# Collapse gate — B4 PromotionGuard NCOM/PIIC integration
# ---------------------------------------------------------------------------


def _base_context() -> dict:
    """Passing Ring-4 context without NCOM/PIIC fields."""
    from ns.services.loom.service import ConfidenceEnvelope

    return {
        "confidence": ConfidenceEnvelope(evidence=0.9, contradiction=0.1, novelty=0.8, stability=0.9),
        "contradiction_weight": 0.10,
        "reconstructability": 0.95,
        "lineage_valid": True,
        "hic_approval": True,
        "pdp_approval": True,
        "quorum_certs": [{"serial": "26116460"}],
        "state": {"coherent": True},
    }


def _collapse_context() -> dict:
    """Passing context including NCOM/PIIC collapse fields."""
    from ns.services.ncom.readiness import CollapseReadiness
    from ns.services.ncom.state import NCOMState
    from ns.services.piic.chain import PIICStage

    ctx = _base_context()
    ctx["ncom_state"] = NCOMState.ready_for_collapse
    ctx["piic_stage"] = PIICStage.commitment
    ctx["readiness"] = CollapseReadiness(
        ERS=0.8, CRS=0.8, IPI=0.6,
        contradictionPressure=0.2, branchDiversityAdequacy=0.7,
    )
    return ctx


class TestCollapseGate:
    def test_promotion_passes_without_ncom_fields(self):
        """Existing Ring-4 context (no NCOM/PIIC) still passes."""
        from ns.services.canon.promotion_guard import PromotionGuard

        assert PromotionGuard().can_promote("br_001", _base_context()) is True

    def test_promotion_passes_with_collapse_ready_ncom(self):
        from ns.services.canon.promotion_guard import PromotionGuard

        assert PromotionGuard().can_promote("br_001", _collapse_context()) is True

    def test_promotion_denied_ncom_not_collapse_ready(self):
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.ncom.state import NCOMState

        ctx = _collapse_context()
        ctx["ncom_state"] = NCOMState.stabilizing
        assert PromotionGuard().can_promote("br_001", ctx) is False

    def test_promotion_denied_piic_not_committed(self):
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.piic.chain import PIICStage

        ctx = _collapse_context()
        ctx["piic_stage"] = PIICStage.identification
        assert PromotionGuard().can_promote("br_001", ctx) is False

    def test_promotion_denied_readiness_action_not_collapse(self):
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.ncom.readiness import CollapseReadiness

        ctx = _collapse_context()
        ctx["readiness"] = CollapseReadiness(ERS=0.1)  # → wait
        assert PromotionGuard().can_promote("br_001", ctx) is False

    def test_promotion_denied_hard_vetoes_present(self):
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.ncom.readiness import CollapseReadiness

        ctx = _collapse_context()
        ctx["readiness"] = CollapseReadiness(
            ERS=0.8, CRS=0.8, IPI=0.6,
            contradictionPressure=0.2, branchDiversityAdequacy=0.7,
            hardVetoes=["lineage_gap_detected"],
        )
        assert PromotionGuard().can_promote("br_001", ctx) is False

    def test_forced_collapse_also_passes_gate(self):
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.ncom.state import NCOMState

        ctx = _collapse_context()
        ctx["ncom_state"] = NCOMState.forced_collapse
        assert PromotionGuard().can_promote("br_001", ctx) is True

    def test_ncom_veto_emitted_receipt_on_veto(self, tmp_path):
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.ncom.state import NCOMState

        ctx = _collapse_context()
        ctx["ncom_state"] = NCOMState.stabilizing
        result = PromotionGuard().promote("br_001", ctx, receipt_path=tmp_path / "r.jsonl")
        assert result["receipt_name"] == "ncom_veto_emitted"
        assert result["allowed"] is False

    def test_veto_reason_in_result_when_vetoed(self):
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.ncom.state import NCOMState

        ctx = _collapse_context()
        ctx["ncom_state"] = NCOMState.observing
        result = PromotionGuard().promote("br_001", ctx)
        assert "veto_reason" in result
        assert "ncom_state_not_collapse_ready" in result["veto_reason"]

    def test_ncom_state_string_accepted(self):
        from ns.services.canon.promotion_guard import PromotionGuard

        ctx = _collapse_context()
        ctx["ncom_state"] = "ready_for_collapse"
        assert PromotionGuard().can_promote("br_001", ctx) is True

    def test_piic_stage_string_accepted(self):
        from ns.services.canon.promotion_guard import PromotionGuard

        ctx = _collapse_context()
        ctx["piic_stage"] = "commitment"
        assert PromotionGuard().can_promote("br_001", ctx) is True


# ---------------------------------------------------------------------------
# Receipt names
# ---------------------------------------------------------------------------


class TestReceiptNames:
    def test_ncom_state_transitioned_in_registry(self):
        from ns.domain.receipts.names import RECEIPT_NAMES

        assert "ncom_state_transitioned" in RECEIPT_NAMES

    def test_piic_stage_advanced_in_registry(self):
        from ns.domain.receipts.names import RECEIPT_NAMES

        assert "piic_stage_advanced" in RECEIPT_NAMES

    def test_ncom_veto_emitted_in_registry(self):
        from ns.domain.receipts.names import RECEIPT_NAMES

        assert "ncom_veto_emitted" in RECEIPT_NAMES
