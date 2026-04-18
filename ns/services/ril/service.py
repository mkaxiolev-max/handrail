"""RIL Evaluator — composes all 8 integrity engines (C4).

Tag: ril-evaluator-v2
"""
from __future__ import annotations

from ns.api.schemas.common import IntegrityRouteEffect, IntegritySummary, RouteIntent
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
    commitment_engine,
    drift_engine,
    encounter_engine,
    founder_loop_breaker,
    grounding_engine,
    interface_recalibration,
    reality_binding_engine,
    rendering_capture,
)


def evaluate(
    tick: int = 0,
    drift_signals: list[DriftSignal] | None = None,
    grounding_observations: list[GroundingObservation] | None = None,
    commitment_records: list[CommitmentRecord] | None = None,
    encounter_records: list[EncounterRecord] | None = None,
    recursion_depth: int = 0,
    reality_bindings: list[RealityBinding] | None = None,
    rendering_captures: list[RenderingCapture] | None = None,
) -> tuple[RILEvaluationResult, IntegritySummary, RouteIntent]:
    ds = drift_signals or []
    go = grounding_observations or []
    cr = commitment_records or []
    er = encounter_records or []
    rb = reality_bindings or []
    rc = rendering_captures or []

    engine_results: list[RILEngineResult] = [
        drift_engine.evaluate(ds, tick=tick),
        grounding_engine.evaluate(go, tick=tick),
        commitment_engine.evaluate(cr, tick=tick),
        encounter_engine.evaluate(er, tick=tick),
        founder_loop_breaker.evaluate(recursion_depth, tick=tick),
        reality_binding_engine.evaluate(rb, go, tick=tick),
        rendering_capture.evaluate(rc, tick=tick),
    ]

    # Aggregate score: mean of all engine scores
    agg_score = round(sum(r.score for r in engine_results) / len(engine_results), 4)
    all_passed = all(r.passed for r in engine_results)

    # Interface recalibration uses the pre-computed aggregate
    recal = interface_recalibration.evaluate(agg_score, tick=tick)
    engine_results.append(recal)

    eval_result = RILEvaluationResult(
        aggregate_score=agg_score,
        engine_results=engine_results,
        all_passed=all_passed,
        tick=tick,
    )

    # Route effect
    if not all_passed:
        blocked = [r for r in engine_results if not r.passed]
        # I19 veto is unconditional escalation
        if any(r.engine_id == "founder_loop_breaker" for r in blocked):
            effect = IntegrityRouteEffect.ESCALATE
        elif agg_score < 0.3:
            effect = IntegrityRouteEffect.BLOCK
        else:
            effect = IntegrityRouteEffect.WARN
    elif agg_score < 0.7:
        effect = IntegrityRouteEffect.WARN
    else:
        effect = IntegrityRouteEffect.PASS

    summary = IntegritySummary(
        aggregate_score=agg_score,
        route_effect=effect,
        engines_evaluated=len(engine_results),
        tick=tick,
    )

    intent_map = {
        IntegrityRouteEffect.PASS: RouteIntent.COMMIT,
        IntegrityRouteEffect.WARN: RouteIntent.CORRECT,
        IntegrityRouteEffect.BLOCK: RouteIntent.OBSERVE,
        IntegrityRouteEffect.ESCALATE: RouteIntent.ESCALATE,
    }
    route_intent = intent_map[effect]

    return eval_result, summary, route_intent
