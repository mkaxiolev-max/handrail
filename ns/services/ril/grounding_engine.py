"""RIL Grounding Engine — validates empirical grounding from Gradient Field (I18, C3).

Requires ≥1 GroundingObservation with confidence ≥ 0.5 to pass.
"""
from __future__ import annotations

from ns.domain.models.integrity import GroundingObservation, RILEngineResult

ENGINE_ID = "grounding_engine"
MIN_CONFIDENCE = 0.5


def evaluate(observations: list[GroundingObservation], tick: int = 0) -> RILEngineResult:
    qualified = [o for o in observations if o.confidence >= MIN_CONFIDENCE]
    if not qualified:
        return RILEngineResult(
            engine_id=ENGINE_ID, score=0.0, passed=False,
            detail="no qualified grounding observations (I18 violation)", tick=tick,
        )
    avg_confidence = sum(o.confidence for o in qualified) / len(qualified)
    score = round(min(1.0, avg_confidence), 4)
    return RILEngineResult(
        engine_id=ENGINE_ID, score=score, passed=True,
        detail=f"qualified_observations={len(qualified)}, avg_confidence={avg_confidence:.4f}",
        tick=tick,
    )
