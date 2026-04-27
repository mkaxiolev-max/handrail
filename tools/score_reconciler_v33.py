"""Score Reconciler v3.3 — composite score with I8 instrument."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json


WEIGHTS_V33 = {
    "I1": 0.15,  # Formal Verification
    "I2": 0.15,  # Risk & Safety
    "I3": 0.10,  # Test Depth
    "I4": 0.10,  # Reversibility
    "I5": 0.10,  # Observability
    "I6": 0.10,  # Alignment
    "I7": 0.20,  # Certification Power
    "I8": 0.10,  # Omega-Prime / Self-Modification
}

assert abs(sum(WEIGHTS_V33.values()) - 1.0) < 1e-9, "Weights must sum to 1.0"


@dataclass
class InstrumentScore:
    instrument: str
    raw: float      # 0–100
    weight: float
    weighted: float


@dataclass
class ReconcilerReport:
    version: str
    scores: list[InstrumentScore]
    composite: float
    band: str
    i8_contribution: float


def _band(score: float) -> str:
    if score < 70:
        return "not_certifiable"
    elif score < 85:
        return "provisional"
    elif score < 92:
        return "audit_ready_internal"
    elif score < 97:
        return "external_certification_ready"
    else:
        return "theoretical_max"


class ScoreReconcilerV33:
    def __init__(self):
        self._raw: dict[str, float] = {}

    def set_instrument(self, instrument: str, score: float) -> None:
        if instrument not in WEIGHTS_V33:
            raise ValueError(f"Unknown instrument: {instrument}. Valid: {list(WEIGHTS_V33)}")
        if not 0.0 <= score <= 100.0:
            raise ValueError(f"Score must be 0–100, got {score}")
        self._raw[instrument] = score

    def reconcile(self) -> ReconcilerReport:
        scores = []
        composite = 0.0
        for inst, w in WEIGHTS_V33.items():
            raw = self._raw.get(inst, 0.0)
            weighted = raw * w
            composite += weighted
            scores.append(InstrumentScore(inst, raw, w, round(weighted, 4)))
        i8_contrib = scores[-1].weighted  # I8 is last
        return ReconcilerReport(
            version="v3.3",
            scores=scores,
            composite=round(composite, 4),
            band=_band(composite),
            i8_contribution=round(i8_contrib, 4),
        )

    def to_dict(self) -> dict:
        r = self.reconcile()
        return {
            "version": r.version,
            "composite": r.composite,
            "band": r.band,
            "i8_contribution": r.i8_contribution,
            "instruments": {s.instrument: {"raw": s.raw, "weight": s.weight, "weighted": s.weighted} for s in r.scores},
        }

    def export(self, path: Path) -> Path:
        path.write_text(json.dumps(self.to_dict(), indent=2))
        return path
