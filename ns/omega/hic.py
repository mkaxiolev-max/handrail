"""
axiolev-omega-hic-v2
AXIOLEV Holdings LLC © 2026

Human Intent Compiler. Canon promotion requires hardware quorum (I4).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class HICDecision:
    intent_id: str
    approved: bool
    rationale: str
    yubikey_serials: List[str]
    receipt_id: Optional[str] = None


def require_quorum(serials: List[str], required: int = 2) -> bool:
    return len(set(serials)) >= required


def compile_intent(
    intent_id: str,
    rationale: str,
    serials: List[str],
    required: int = 2,
) -> HICDecision:
    ok = require_quorum(serials, required=required)
    return HICDecision(
        intent_id=intent_id,
        approved=ok,
        rationale=rationale,
        yubikey_serials=list(serials),
    )
