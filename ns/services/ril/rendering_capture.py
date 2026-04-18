"""RIL Rendering Capture — audit trail for Narrative Interface outputs (L10, C3).

Captures rendered text and verifies it is anchored to observations.
"""
from __future__ import annotations

from ns.domain.models.integrity import RenderingCapture, RILEngineResult

ENGINE_ID = "rendering_capture"


def evaluate(captures: list[RenderingCapture], tick: int = 0) -> RILEngineResult:
    if not captures:
        return RILEngineResult(engine_id=ENGINE_ID, score=1.0, passed=True,
                               detail="no captures to evaluate", tick=tick)

    unanchored = [c for c in captures if not c.bound_observation_ids]
    if unanchored:
        score = round(1.0 - (len(unanchored) / len(captures)), 4)
        return RILEngineResult(
            engine_id=ENGINE_ID,
            score=max(0.0, score),
            passed=False,
            detail=f"unanchored_captures={len(unanchored)} of {len(captures)}",
            tick=tick,
        )

    return RILEngineResult(engine_id=ENGINE_ID, score=1.0, passed=True,
                           detail=f"captures_verified={len(captures)}", tick=tick)
