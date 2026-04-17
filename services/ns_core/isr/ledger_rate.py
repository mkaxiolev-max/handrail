"""Pure math over Alexandria receipts — no network, no LLM."""
from __future__ import annotations

from typing import Any, Dict, List


def compute_ledger_rate(receipts: List[Dict[str, Any]], window_minutes: int = 15) -> float:
    """Narrative-token emission rate per minute in window.

    Pure function of receipt list. Deterministic. No side effects.
    """
    if not receipts:
        return 0.0
    narrative_tokens = sum(
        r.get("tokens_output", 0) + r.get("narrative_tokens", 0)
        for r in receipts
    )
    grounded_actions = sum(
        1 for r in receipts if r.get("grounded", False) or r.get("receipt_id")
    )
    grounded_actions = max(grounded_actions, 1)
    rate = narrative_tokens / (window_minutes * grounded_actions)
    return round(rate, 6)
