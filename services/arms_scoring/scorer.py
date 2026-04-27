"""ARMS — Autonomous Risk Management Scoring suite."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import math


class RiskDimension(str, Enum):
    OPERATIONAL = "operational"
    REPUTATIONAL = "reputational"
    LEGAL = "legal"
    TECHNICAL = "technical"
    CONSTITUTIONAL = "constitutional"


DIMENSION_WEIGHTS = {
    RiskDimension.OPERATIONAL: 0.25,
    RiskDimension.REPUTATIONAL: 0.20,
    RiskDimension.LEGAL: 0.20,
    RiskDimension.TECHNICAL: 0.20,
    RiskDimension.CONSTITUTIONAL: 0.15,
}


@dataclass
class RiskScore:
    dimension: RiskDimension
    raw: float        # 0–10
    weighted: float
    mitigated: bool


@dataclass
class ARMSReport:
    scores: list[RiskScore]
    composite: float
    band: str
    mitigated_count: int


def _band(composite: float) -> str:
    if composite < 3.0:
        return "green"
    elif composite < 6.0:
        return "amber"
    else:
        return "red"


class ARMSScorer:
    def __init__(self):
        self._scores: dict[RiskDimension, float] = {}
        self._mitigations: set[RiskDimension] = set()

    def set_score(self, dimension: RiskDimension, raw: float) -> None:
        if not 0.0 <= raw <= 10.0:
            raise ValueError(f"Score must be 0–10, got {raw}")
        self._scores[dimension] = raw

    def add_mitigation(self, dimension: RiskDimension) -> None:
        self._mitigations.add(dimension)

    def report(self) -> ARMSReport:
        scores = []
        for dim in RiskDimension:
            raw = self._scores.get(dim, 5.0)
            effective = raw * 0.5 if dim in self._mitigations else raw
            w = DIMENSION_WEIGHTS[dim]
            scores.append(RiskScore(dim, raw, round(effective * w, 3), dim in self._mitigations))
        composite = round(sum(s.weighted for s in scores), 3)
        return ARMSReport(
            scores=scores,
            composite=composite,
            band=_band(composite),
            mitigated_count=len(self._mitigations),
        )
