"""RIL Commitment Engine — tracks proposition commitment strength (C3).

A CommitmentRecord with strength ≥ 0.7 and committed=True is required to pass.
"""
from __future__ import annotations

from ns.domain.models.integrity import CommitmentRecord, RILEngineResult

ENGINE_ID = "commitment_engine"
MIN_STRENGTH = 0.7


def evaluate(records: list[CommitmentRecord], tick: int = 0) -> RILEngineResult:
    if not records:
        return RILEngineResult(engine_id=ENGINE_ID, score=1.0, passed=True,
                               detail="no commitments to evaluate", tick=tick)

    committed = [r for r in records if r.committed and r.strength >= MIN_STRENGTH]
    uncommitted_high = [r for r in records if not r.committed and r.strength >= MIN_STRENGTH]

    if uncommitted_high:
        score = 0.4
        return RILEngineResult(engine_id=ENGINE_ID, score=score, passed=False,
                               detail=f"uncommitted high-strength records={len(uncommitted_high)}",
                               tick=tick)

    avg_strength = (sum(r.strength for r in records) / len(records)) if records else 1.0
    score = round(min(1.0, avg_strength), 4)
    return RILEngineResult(engine_id=ENGINE_ID, score=score, passed=True,
                           detail=f"committed={len(committed)}, total={len(records)}", tick=tick)
