"""Narrative Energy Rate (NER) observable.

Pure function of the ledger. No LLM call. No network.
Returns ReturnBlock.v2 wrapping {rate, trend, threshold_crossed}.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from isr.ledger_rate import compute_ledger_rate

_NER_THRESHOLD_DEFAULT = 3.0


def _load_threshold() -> float:
    try:
        canon_path = os.environ.get(
            "CANON_ROOT",
            os.path.abspath(os.path.join(os.getcwd(), "canon"))
        )
        ax_path = os.path.join(canon_path, "axioms/ax_core.json")
        if os.path.exists(ax_path):
            with open(ax_path) as f:
                return float(json.load(f).get("ner_threshold", _NER_THRESHOLD_DEFAULT))
    except Exception:
        pass
    return _NER_THRESHOLD_DEFAULT


class NERObservation(BaseModel):
    rate: float
    trend: str  # "stable", "rising", "falling"
    threshold_crossed: bool
    window_minutes: int
    receipt_count: int
    threshold: float


def compute_ner(
    receipts: List[Dict[str, Any]],
    window_minutes: int = 15,
    prior_rate: Optional[float] = None,
) -> NERObservation:
    """Pure function. Deterministic. No side effects."""
    threshold = _load_threshold()
    rate = compute_ledger_rate(receipts, window_minutes)

    if prior_rate is None:
        trend = "stable"
    elif rate > prior_rate * 1.1:
        trend = "rising"
    elif rate < prior_rate * 0.9:
        trend = "falling"
    else:
        trend = "stable"

    return NERObservation(
        rate=rate,
        trend=trend,
        threshold_crossed=(rate >= threshold),
        window_minutes=window_minutes,
        receipt_count=len(receipts),
        threshold=threshold,
    )
