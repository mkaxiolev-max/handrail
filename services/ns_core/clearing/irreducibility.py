"""CI-3 Irreducibility — guards against lossy receipt chain compression."""
from __future__ import annotations

from typing import Any, Dict, List


class Irreducibility:
    def __init__(self, min_receipts: int = 3):
        self._min_receipts = min_receipts

    def evaluate(self, candidate: dict) -> bool:
        """Returns True (must abstain) when query would cause lossy compression.

        Lossy compression occurs when:
        - candidate requests a summary that drops receipt chain entries
        - candidate has fewer source receipts than the minimum required
        """
        receipts = candidate.get("receipts", candidate.get("source_receipts", []))
        if isinstance(receipts, list) and len(receipts) > 0:
            if len(receipts) < self._min_receipts:
                return True
        # Detect explicit compression request
        if candidate.get("compress") or candidate.get("summarize_lossy"):
            return True
        return False
