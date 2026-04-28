"""Weighted aggregator; threshold=0.65; emits DecoherenceDetector."""
from __future__ import annotations
from services.coherence_kernel import schemas
from services.coherence_kernel.decoherence import (
    urgency, bias, context_loss, narrative_lock, social_pressure,
)
from services.coherence_kernel.storage import ledger

_WEIGHTS = {
    "urgency": 0.25,
    "bias": 0.20,
    "context_loss": 0.20,
    "narrative_lock": 0.20,
    "social_pressure": 0.15,
}
THRESHOLD = 0.65


def detect(branch: schemas.BranchState) -> schemas.DecoherenceDetector:
    u = urgency.score(branch)
    b = bias.score(branch)
    c = context_loss.score(branch)
    n = narrative_lock.score(branch)
    s = social_pressure.score(branch)

    agg = round(
        u * _WEIGHTS["urgency"]
        + b * _WEIGHTS["bias"]
        + c * _WEIGHTS["context_loss"]
        + n * _WEIGHTS["narrative_lock"]
        + s * _WEIGHTS["social_pressure"],
        6,
    )

    det = schemas.DecoherenceDetector(
        urgency_score=u,
        bias_score=b,
        context_loss_score=c,
        narrative_lock_score=n,
        social_pressure_score=s,
        aggregate=agg,
        threshold=THRESHOLD,
        breached=agg >= THRESHOLD,
    )
    if det.breached:
        ledger.append_decoherence_event(det.model_dump(mode="json"), branch.id)
    return det
