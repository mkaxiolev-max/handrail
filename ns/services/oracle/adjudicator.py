"""Oracle v2 adjudicator — two-stage adjudication pipeline (C6).

Stage 1: Constitutional overlay (never-events, G₂, dignity kernel)
Stage 2: Policy matrix + RIL route effect → OracleDecision

Tag: oracle-v2-adjudicator-v2
"""
from __future__ import annotations

from ns.api.schemas.oracle import (
    OracleAdjudicationRequest,
    OracleAdjudicationResponse,
)
from ns.services.oracle import constitutional_overlays, decision_selector, envelope_builder, founder_translation, trace_builder


def adjudicate(req: OracleAdjudicationRequest) -> OracleAdjudicationResponse:
    receipts: list[str] = []

    # Stage 1a — never-event screen
    ne_blocking = constitutional_overlays.check_never_events(req.constitutional_context)

    # Stage 1b — G₂ 3-form coherence check
    g2_ok, g2_blocking = constitutional_overlays.check_g2_phi(req)
    receipts.append("ring6_g2_invariant_checked")

    # Stage 1c — envelope conditions (YubiKey gate, risk tier)
    conditions = envelope_builder.build_conditions(req.envelope)
    cond_blocking = envelope_builder.blocking_from_conditions(conditions)

    all_blocking = ne_blocking + g2_blocking + cond_blocking

    # Stage 2 — decision selection
    decision = decision_selector.select_decision(all_blocking, req.ril_route_effect)
    severity = decision_selector.select_severity(all_blocking, decision)

    receipts.append(f"oracle_decision_{decision.value.lower()}")

    translation = founder_translation.translate(decision, severity)

    trace = trace_builder.build_trace(
        request_id=req.request_id,
        conditions=conditions,
        blocking_reasons=all_blocking,
        decision=decision,
        severity=severity,
        g2_parallel=g2_ok,
    )

    return OracleAdjudicationResponse(
        request_id=req.request_id,
        decision=decision,
        severity=severity,
        conditions_checked=conditions,
        blocking_reasons=all_blocking,
        route_intent=_route_intent(decision),
        receipts_emitted=receipts,
        founder_translation=translation,
        trace=trace,
        tick=req.tick,
    )


def _route_intent(decision):
    from ns.api.schemas.common import RouteIntent
    return {
        "ALLOW": RouteIntent.COMMIT,
        "DEFER": RouteIntent.CORRECT,
        "DENY": RouteIntent.OBSERVE,
        "ESCALATE": RouteIntent.ESCALATE,
    }[decision.value]
