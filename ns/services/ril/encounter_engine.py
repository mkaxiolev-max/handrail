"""RIL Encounter Engine — handles contradiction encounters (C3).

Unresolved encounters with contradiction_weight > 0.5 → BLOCK.
"""
from __future__ import annotations

from ns.domain.models.integrity import EncounterRecord, RILEngineResult

ENGINE_ID = "encounter_engine"
BLOCK_THRESHOLD = 0.5


def evaluate(encounters: list[EncounterRecord], tick: int = 0) -> RILEngineResult:
    if not encounters:
        return RILEngineResult(engine_id=ENGINE_ID, score=1.0, passed=True, tick=tick)

    blocking = [e for e in encounters if not e.resolved and e.contradiction_weight > BLOCK_THRESHOLD]
    if blocking:
        worst = max(e.contradiction_weight for e in blocking)
        return RILEngineResult(
            engine_id=ENGINE_ID,
            score=round(1.0 - worst, 4),
            passed=False,
            detail=f"unresolved_blocking={len(blocking)}, worst_weight={worst:.4f}",
            tick=tick,
        )

    resolved_ratio = sum(1 for e in encounters if e.resolved) / len(encounters)
    return RILEngineResult(engine_id=ENGINE_ID, score=round(resolved_ratio, 4),
                           passed=True, detail=f"resolved_ratio={resolved_ratio:.4f}", tick=tick)
