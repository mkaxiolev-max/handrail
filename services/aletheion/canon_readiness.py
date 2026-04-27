"""Aletheion v2.0 — Canon readiness assessment."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from pydantic import BaseModel


class CanonReadinessRequest(BaseModel):
    claim_id: str
    evidence_refs: List[str] = []
    contradiction_score: float = 0.0
    admissibility_score: float = 1.0
    constraint_score: float = 1.0
    logos_score: float = 1.0
    narrative_contamination_risk: float = 0.0


@dataclass
class CanonReadinessResponse:
    decision: str  # ALLOW | DENY | WITHHOLD
    canon_readiness_score: float
    reasons: List[str] = field(default_factory=list)


def assess_canon_readiness(req: CanonReadinessRequest) -> CanonReadinessResponse:
    reasons: List[str] = []

    score = (
        req.admissibility_score * 0.30
        + req.constraint_score * 0.25
        + req.logos_score * 0.25
        + (1.0 - req.contradiction_score) * 0.10
        + (1.0 - req.narrative_contamination_risk) * 0.10
    ) * 100.0

    if req.contradiction_score >= 0.8:
        reasons.append(f"contradiction_score={req.contradiction_score:.2f} too high")
        decision = "DENY"
    elif req.narrative_contamination_risk >= 0.7:
        reasons.append(f"narrative_contamination_risk={req.narrative_contamination_risk:.2f}")
        decision = "WITHHOLD"
    elif score >= 70.0:
        decision = "ALLOW"
    else:
        reasons.append(f"readiness_score={score:.2f} < 70")
        decision = "DENY"

    return CanonReadinessResponse(
        decision=decision,
        canon_readiness_score=round(score, 2),
        reasons=reasons,
    )
