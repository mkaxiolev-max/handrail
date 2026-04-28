"""Urgency sub-detector: measures time-pressure-driven coherence degradation."""
from __future__ import annotations
from services.coherence_kernel import schemas


def score(branch: schemas.BranchState) -> float:
    """High urgency when reversibility_cost is high and uncertainty is high."""
    rev_norm = min(1.0, branch.reversibility_cost / 10.0)
    return round((rev_norm + branch.uncertainty) / 2.0, 6)
