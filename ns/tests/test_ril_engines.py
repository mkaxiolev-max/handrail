"""RIL engine tests — ≥6 tests covering C2/C3/C4 (ril-P2).

Tag: ril-oracle-tests-green-v2
"""
from __future__ import annotations

import pytest

from ns.api.schemas.common import IntegrityRouteEffect, IntegritySummary, RouteIntent, ReflexiveIntegrityState
from ns.api.schemas.ril import RILEvaluateRequest, RILEvaluateResponse
from ns.domain.models.integrity import (
    CommitmentRecord,
    DriftSignal,
    EncounterRecord,
    GroundingObservation,
    RealityBinding,
    RenderingCapture,
    RILEngineResult,
    RILEvaluationResult,
)
from ns.services.ril import (
    drift_engine,
    grounding_engine,
    commitment_engine,
    encounter_engine,
    founder_loop_breaker,
    reality_binding_engine,
    rendering_capture,
    interface_recalibration,
)
from ns.services.ril import service as ril_service


# ---------------------------------------------------------------------------
# T1 — DriftEngine
# ---------------------------------------------------------------------------

class TestDriftEngine:
    def test_high_drift_blocks(self):
        signals = [DriftSignal(signal_id="s1", magnitude=0.9, layer="L2_gradient")]
        result = drift_engine.evaluate(signals)
        assert not result.passed
        assert result.score < 0.5

    def test_low_drift_passes(self):
        signals = [DriftSignal(signal_id="s2", magnitude=0.1, layer="L2_gradient")]
        result = drift_engine.evaluate(signals)
        assert result.passed
        assert result.score >= 0.4

    def test_suppressed_signals_ignored(self):
        signals = [DriftSignal(signal_id="s3", magnitude=0.95, layer="L2_gradient", suppressed=True)]
        result = drift_engine.evaluate(signals)
        assert result.passed
        assert result.score == 1.0

    def test_no_signals_passes(self):
        result = drift_engine.evaluate([])
        assert result.passed
        assert result.score == 1.0


# ---------------------------------------------------------------------------
# T2 — GroundingEngine
# ---------------------------------------------------------------------------

class TestGroundingEngine:
    def test_no_observations_fails(self):
        result = grounding_engine.evaluate([])
        assert not result.passed
        assert result.score == 0.0

    def test_low_confidence_observation_fails(self):
        obs = [GroundingObservation(observation_id="o1", content="x", confidence=0.3)]
        result = grounding_engine.evaluate(obs)
        assert not result.passed

    def test_high_confidence_observation_passes(self):
        obs = [GroundingObservation(observation_id="o2", content="y", confidence=0.8)]
        result = grounding_engine.evaluate(obs)
        assert result.passed
        assert result.score >= 0.8


# ---------------------------------------------------------------------------
# T3 — FounderLoopBreaker (I19)
# ---------------------------------------------------------------------------

class TestFounderLoopBreaker:
    def test_depth_zero_passes(self):
        result = founder_loop_breaker.evaluate(0)
        assert result.passed
        assert result.score == 1.0

    def test_depth_three_passes(self):
        result = founder_loop_breaker.evaluate(3)
        assert result.passed

    def test_depth_four_blocks(self):
        result = founder_loop_breaker.evaluate(4)
        assert not result.passed
        assert result.score == 0.0
        assert "I19" in (result.detail or "")

    def test_depth_ten_blocks(self):
        result = founder_loop_breaker.evaluate(10)
        assert not result.passed


# ---------------------------------------------------------------------------
# T4 — RealityBindingEngine (I18)
# ---------------------------------------------------------------------------

class TestRealityBindingEngine:
    def test_binding_with_no_observation_fails(self):
        binding = RealityBinding(binding_id="b1", observation_ids=["missing_obs"], is_bound=False)
        result = reality_binding_engine.evaluate([binding], [])
        assert not result.passed
        assert "I18" in (result.detail or "")

    def test_binding_with_matching_observation_passes(self):
        obs = GroundingObservation(observation_id="o1", content="fact", confidence=0.9)
        binding = RealityBinding(binding_id="b1", observation_ids=["o1"], is_bound=True)
        result = reality_binding_engine.evaluate([binding], [obs])
        assert result.passed

    def test_no_bindings_trivially_passes(self):
        result = reality_binding_engine.evaluate([], [])
        assert result.passed
        assert result.score == 1.0


# ---------------------------------------------------------------------------
# T5 — CommitmentEngine
# ---------------------------------------------------------------------------

class TestCommitmentEngine:
    def test_uncommitted_high_strength_fails(self):
        rec = CommitmentRecord(commitment_id="c1", proposition="P", committed=False, strength=0.9)
        result = commitment_engine.evaluate([rec])
        assert not result.passed

    def test_committed_record_passes(self):
        rec = CommitmentRecord(commitment_id="c2", proposition="Q", committed=True, strength=0.8)
        result = commitment_engine.evaluate([rec])
        assert result.passed

    def test_empty_records_passes(self):
        result = commitment_engine.evaluate([])
        assert result.passed


# ---------------------------------------------------------------------------
# T6 — EncounterEngine
# ---------------------------------------------------------------------------

class TestEncounterEngine:
    def test_unresolved_heavy_encounter_fails(self):
        enc = EncounterRecord(encounter_id="e1", contradiction_weight=0.9, resolved=False)
        result = encounter_engine.evaluate([enc])
        assert not result.passed

    def test_resolved_encounter_passes(self):
        enc = EncounterRecord(encounter_id="e2", contradiction_weight=0.9, resolved=True, resolution_tick=1)
        result = encounter_engine.evaluate([enc])
        assert result.passed

    def test_no_encounters_passes(self):
        result = encounter_engine.evaluate([])
        assert result.passed


# ---------------------------------------------------------------------------
# T7 — RenderingCapture
# ---------------------------------------------------------------------------

class TestRenderingCapture:
    def test_unanchored_capture_fails(self):
        cap = RenderingCapture(capture_id="cap1", rendered_text="hello", bound_observation_ids=[])
        result = rendering_capture.evaluate([cap])
        assert not result.passed

    def test_anchored_capture_passes(self):
        cap = RenderingCapture(capture_id="cap2", rendered_text="hello", bound_observation_ids=["o1"])
        result = rendering_capture.evaluate([cap])
        assert result.passed

    def test_no_captures_passes(self):
        result = rendering_capture.evaluate([])
        assert result.passed


# ---------------------------------------------------------------------------
# T8 — InterfaceRecalibration
# ---------------------------------------------------------------------------

class TestInterfaceRecalibration:
    def test_low_score_triggers_recalibration(self):
        result = interface_recalibration.evaluate(0.3)
        assert result.passed  # recalibration always passes
        assert "recalibration_triggered" in (result.detail or "")

    def test_high_score_stable(self):
        result = interface_recalibration.evaluate(0.9)
        assert result.passed
        assert "interface_stable" in (result.detail or "")

    def test_invalid_score_raises(self):
        with pytest.raises(ValueError):
            interface_recalibration.evaluate(1.5)


# ---------------------------------------------------------------------------
# T9 — RIL Service (C4 composition)
# ---------------------------------------------------------------------------

class TestRILService:
    def test_all_pass_produces_commit_intent(self):
        obs = [GroundingObservation(observation_id="o1", content="fact", confidence=0.9)]
        eval_result, summary, intent = ril_service.evaluate(
            tick=1,
            grounding_observations=obs,
        )
        assert eval_result.all_passed
        assert summary.route_effect == IntegrityRouteEffect.PASS
        assert intent == RouteIntent.COMMIT

    def test_high_drift_produces_non_pass(self):
        signals = [DriftSignal(signal_id="s1", magnitude=0.95, layer="L2")]
        _, summary, intent = ril_service.evaluate(tick=2, drift_signals=signals)
        assert summary.route_effect != IntegrityRouteEffect.PASS

    def test_i19_violation_escalates(self):
        _, summary, intent = ril_service.evaluate(tick=3, recursion_depth=5)
        assert summary.route_effect == IntegrityRouteEffect.ESCALATE
        assert intent == RouteIntent.ESCALATE

    def test_aggregate_score_in_range(self):
        eval_result, summary, _ = ril_service.evaluate(tick=4)
        assert 0.0 <= eval_result.aggregate_score <= 1.0
        assert 0.0 <= summary.aggregate_score <= 1.0

    def test_engines_evaluated_count(self):
        _, summary, _ = ril_service.evaluate(tick=5)
        assert summary.engines_evaluated == 8  # 7 gating + 1 recalibration


# ---------------------------------------------------------------------------
# T10 — Domain model validators
# ---------------------------------------------------------------------------

class TestDomainModelValidators:
    def test_drift_signal_magnitude_out_of_range_raises(self):
        with pytest.raises(Exception):
            DriftSignal(signal_id="bad", magnitude=1.5, layer="L2")

    def test_grounding_confidence_out_of_range_raises(self):
        with pytest.raises(Exception):
            GroundingObservation(observation_id="bad", content="x", confidence=-0.1)

    def test_ril_engine_result_score_out_of_range_raises(self):
        with pytest.raises(Exception):
            RILEngineResult(engine_id="x", score=2.0, passed=True)

    def test_ril_evaluation_result_extra_forbid(self):
        with pytest.raises(Exception):
            RILEvaluationResult(
                aggregate_score=0.5,
                engine_results=[],
                all_passed=True,
                tick=0,
                unexpected_field="oops",
            )


# ---------------------------------------------------------------------------
# T11 — API schema round-trip
# ---------------------------------------------------------------------------

class TestAPISchemas:
    def test_reflexive_integrity_state_roundtrip(self):
        state = ReflexiveIntegrityState(
            engine_id="drift_engine", score=0.8,
            effect=IntegrityRouteEffect.PASS, tick=1,
        )
        assert state.effect == IntegrityRouteEffect.PASS
        d = state.model_dump()
        restored = ReflexiveIntegrityState(**d)
        assert restored == state

    def test_integrity_summary_route_effects(self):
        for effect in IntegrityRouteEffect:
            summary = IntegritySummary(
                aggregate_score=0.5, route_effect=effect, engines_evaluated=8,
            )
            assert summary.route_effect == effect

    def test_ril_evaluate_request_defaults(self):
        req = RILEvaluateRequest()
        assert req.tick == 0
        assert req.recursion_depth == 0
        assert req.drift_signals == []
        assert req.grounding_observations == []
