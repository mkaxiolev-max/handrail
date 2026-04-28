"""Bias sub-detector: measures source homogeneity / confirmation bias."""
from __future__ import annotations
from services.coherence_kernel import schemas


def score(branch: schemas.BranchState) -> float:
    """Low source diversity + high redundancy → high bias score."""
    div_inv = 1.0 - branch.evidence_amplitude.source_diversity
    redund = min(1.0, branch.evidence_amplitude.redundancy_count / 10.0)
    return round((div_inv + redund) / 2.0, 6)
