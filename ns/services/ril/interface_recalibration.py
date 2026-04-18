"""RIL Interface Recalibration — adjusts interface state after RIL evaluation (C3).

Emits a recalibration signal when aggregate score < 0.5.
"""
from __future__ import annotations

from ns.domain.models.integrity import RILEngineResult

ENGINE_ID = "interface_recalibration"
RECALIBRATION_THRESHOLD = 0.5


def evaluate(aggregate_score: float, tick: int = 0) -> RILEngineResult:
    if not 0.0 <= aggregate_score <= 1.0:
        raise ValueError("aggregate_score must be in [0.0, 1.0]")

    needs_recalibration = aggregate_score < RECALIBRATION_THRESHOLD
    score = round(aggregate_score, 4)
    detail = (
        f"recalibration_triggered (score={score})"
        if needs_recalibration
        else f"interface_stable (score={score})"
    )
    # Recalibration itself always passes — it's a corrective action, not a gate
    return RILEngineResult(engine_id=ENGINE_ID, score=score, passed=True,
                           detail=detail, tick=tick)
