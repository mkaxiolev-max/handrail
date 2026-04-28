"""Social-pressure sub-detector: measures cps_op_chain length as proxy for external forcing."""
from __future__ import annotations
from services.coherence_kernel import schemas

_MAX_CHAIN = 8


def score(branch: schemas.BranchState) -> float:
    """Long op chain without intermediate interference → social pressure."""
    chain_len = len(branch.cps_op_chain)
    return round(min(1.0, chain_len / _MAX_CHAIN), 6)
