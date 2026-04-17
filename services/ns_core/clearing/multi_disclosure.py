"""CI-4 MultiDisclosure — multiple truthful framings may coexist."""
from __future__ import annotations

from typing import Any, Dict, List


class MultiDisclosure:
    def evaluate(self, candidate: dict, framings: List[Dict[str, Any]]) -> Dict:
        """When multiple framings are both receipt-consistent, surface both.

        Returns a dict with:
        - multi_framing: True if multiple framings exist
        - framings: the list surfaced for the caller
        - abstain: False (multi-disclosure never abstracts — it surfaces both)
        """
        consistent = [f for f in framings if f.get("receipt_consistent", False)]
        if len(consistent) >= 2:
            return {"multi_framing": True, "framings": consistent, "abstain": False}
        return {"multi_framing": False, "framings": consistent, "abstain": False}
