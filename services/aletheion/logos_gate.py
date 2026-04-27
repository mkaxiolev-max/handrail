"""Aletheion v2.0 — Logos constraint gate."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from pydantic import BaseModel


class LogosConstraintCheck(BaseModel):
    subject_id: str
    truth_coherence: float = 1.0
    dignity_preservation: float = 1.0
    humility_alignment: float = 1.0
    love_vector: float = 1.0
    coercion_risk: float = 0.0
    domination_risk: float = 0.0
    deception_risk: float = 0.0
    sacred_language_override_risk: float = 0.0
    context: dict = {}


@dataclass
class LogosGateResult:
    decision: str  # ALLOW | HARD_STOP | WITHHOLD
    reasons: List[str] = field(default_factory=list)
    receipt_id: Optional[str] = None


def logos_gate(check: LogosConstraintCheck) -> LogosGateResult:
    reasons: List[str] = []

    risk_total = (
        check.coercion_risk
        + check.domination_risk
        + check.deception_risk
        + check.sacred_language_override_risk
    )
    coherence_min = min(
        check.truth_coherence,
        check.dignity_preservation,
        check.humility_alignment,
    )

    if risk_total >= 2.0 or coherence_min < 0.3:
        decision = "HARD_STOP"
        reasons.append(f"risk_total={risk_total:.2f} coherence_min={coherence_min:.2f}")
    elif risk_total >= 1.0 or coherence_min < 0.6:
        decision = "WITHHOLD"
        reasons.append(f"marginal: risk_total={risk_total:.2f}")
    else:
        decision = "ALLOW"

    return LogosGateResult(decision=decision, reasons=reasons, receipt_id=check.subject_id)
