"""Context-loss sub-detector: measures provenance depth insufficiency."""
from __future__ import annotations
from services.coherence_kernel import schemas

_MIN_PROV = 3


def score(branch: schemas.BranchState) -> float:
    """Short provenance chain = high context loss."""
    depth = len(branch.evidence_amplitude.provenance_chain)
    shortfall = max(0, _MIN_PROV - depth) / _MIN_PROV
    return round(shortfall, 6)
