"""RIL Drift Engine — detects semantic drift from Gradient Field baseline (L2, C3).

Drift magnitude ≥ 0.6 → BLOCK. Suppressed signals are skipped.
"""
from __future__ import annotations

from ns.api.schemas.common import IntegrityRouteEffect
from ns.domain.models.integrity import DriftSignal, RILEngineResult

ENGINE_ID = "drift_engine"
DRIFT_BLOCK_THRESHOLD = 0.6


def evaluate(signals: list[DriftSignal], tick: int = 0) -> RILEngineResult:
    active = [s for s in signals if not s.suppressed]
    if not active:
        return RILEngineResult(engine_id=ENGINE_ID, score=1.0, passed=True, tick=tick)

    max_magnitude = max(s.magnitude for s in active)
    score = round(1.0 - max_magnitude, 4)
    passed = max_magnitude < DRIFT_BLOCK_THRESHOLD
    detail = f"max_drift={max_magnitude:.4f}, active_signals={len(active)}"
    return RILEngineResult(engine_id=ENGINE_ID, score=max(0.0, score), passed=passed,
                           detail=detail, tick=tick)
