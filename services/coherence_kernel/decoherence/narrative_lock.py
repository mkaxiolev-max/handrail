"""Narrative-lock sub-detector: measures over-reinforcement without contradiction."""
from __future__ import annotations
from services.coherence_kernel import schemas


def score(branch: schemas.BranchState) -> float:
    """Many reinforcements + no contradictions → narrative lock."""
    reinf = len(branch.reinforcement_links)
    contra = len(branch.contradiction_links)
    if reinf == 0:
        return 0.0
    ratio = reinf / max(reinf + contra, 1)
    return round(min(1.0, ratio), 6)
