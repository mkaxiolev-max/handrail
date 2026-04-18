"""RIL Founder Loop Breaker — enforces I19: recursion depth ≤ 3 (C3).

Any recursion depth > 3 is unconditionally vetoed per I19.
"""
from __future__ import annotations

from ns.domain.models.integrity import RILEngineResult
from ns.domain.models.invariants import I19_founder_loop_protection

ENGINE_ID = "founder_loop_breaker"
MAX_DEPTH = 3


def evaluate(recursion_depth: int, tick: int = 0) -> RILEngineResult:
    passed = I19_founder_loop_protection(recursion_depth, MAX_DEPTH)
    if not passed:
        return RILEngineResult(
            engine_id=ENGINE_ID,
            score=0.0,
            passed=False,
            detail=f"recursion_depth={recursion_depth} exceeds max={MAX_DEPTH} (I19 veto)",
            tick=tick,
        )
    score = round(1.0 - (recursion_depth / (MAX_DEPTH + 1)), 4)
    return RILEngineResult(engine_id=ENGINE_ID, score=max(0.0, score), passed=True,
                           detail=f"recursion_depth={recursion_depth}", tick=tick)
