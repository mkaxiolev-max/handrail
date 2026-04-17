"""CI-1 NonTotalization — refuses to answer 'is X fully determined?' when residual
ambiguity exceeds theta. Forces /pi/check to set abstention=True."""
from __future__ import annotations

_THETA = 0.15  # residual entropy threshold above which totalization is refused


class NonTotalization:
    def __init__(self, theta: float = _THETA):
        self._theta = theta

    def evaluates(self, candidate: dict, residual_entropy: float) -> bool:
        """Returns True (must abstain) when residual entropy > theta."""
        if residual_entropy > self._theta:
            return True
        # Also refuse if candidate explicitly claims full determination
        if candidate.get("claims_full_determination"):
            return True
        return False
