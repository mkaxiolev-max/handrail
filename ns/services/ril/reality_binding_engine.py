"""RIL Reality Binding Engine — enforces I18: narrative binds to ≥1 observation (C3).

All narrative outputs must bind to ≥1 verifiable Gradient Field observation.
"""
from __future__ import annotations

from ns.domain.models.integrity import GroundingObservation, RealityBinding, RILEngineResult
from ns.domain.models.invariants import I18_reality_binding_integrity

ENGINE_ID = "reality_binding_engine"


def evaluate(
    bindings: list[RealityBinding],
    observations: list[GroundingObservation],
    tick: int = 0,
) -> RILEngineResult:
    observation_ids = {o.observation_id for o in observations}

    if not bindings:
        # No narrative output yet — trivially satisfied
        return RILEngineResult(engine_id=ENGINE_ID, score=1.0, passed=True,
                               detail="no bindings to evaluate", tick=tick)

    violations = []
    for b in bindings:
        matched = [oid for oid in b.observation_ids if oid in observation_ids]
        if not I18_reality_binding_integrity(len(matched)):
            violations.append(b.binding_id)

    if violations:
        return RILEngineResult(
            engine_id=ENGINE_ID,
            score=0.0,
            passed=False,
            detail=f"unbound_narratives={violations} (I18 violation)",
            tick=tick,
        )

    score = round(1.0 - (len([b for b in bindings if not b.is_bound]) / len(bindings)), 4)
    return RILEngineResult(engine_id=ENGINE_ID, score=max(0.0, score), passed=True,
                           detail=f"bindings_checked={len(bindings)}", tick=tick)
