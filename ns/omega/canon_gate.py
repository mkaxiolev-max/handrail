"""
axiolev-omega-canon-gate-v2
AXIOLEV Holdings LLC © 2026

Six-fold Canon gate. I1: Canon precedes Conversion.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List

from .primitives import ConfidenceEnvelope


SCORE_THRESHOLD = 0.82
CONTRADICTION_CEILING = 0.25
RECONSTRUCT_THRESHOLD = 0.90


@dataclass(frozen=True)
class CanonGateDecision:
    allowed: bool
    reasons: List[str]


def canon_gate(
    confidence: ConfidenceEnvelope,
    reconstructability: float,
    lineage_valid: bool,
    hic_receipt: Optional[str],
    pdp_receipt: Optional[str],
) -> CanonGateDecision:
    reasons = []
    if confidence.score < SCORE_THRESHOLD:
        reasons.append(f"score {confidence.score:.3f} < {SCORE_THRESHOLD}")
    if confidence.contradiction > CONTRADICTION_CEILING:
        reasons.append(f"contradiction {confidence.contradiction:.3f} > {CONTRADICTION_CEILING}")
    if reconstructability < RECONSTRUCT_THRESHOLD:
        reasons.append(f"reconstructability {reconstructability:.3f} < {RECONSTRUCT_THRESHOLD}")
    if not lineage_valid:
        reasons.append("lineage invalid")
    if not hic_receipt:
        reasons.append("HIC receipt missing")
    if not pdp_receipt:
        reasons.append("PDP receipt missing")
    return CanonGateDecision(allowed=not reasons, reasons=reasons)
