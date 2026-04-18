"""Translates Oracle decisions into founder-readable plain-language (C6).

Tag: oracle-v2-adjudicator-v2
"""
from __future__ import annotations

from ns.api.schemas.oracle import OracleDecision, OracleSeverity


_TRANSLATIONS: dict[tuple, str] = {
    (OracleDecision.ALLOW, OracleSeverity.NOMINAL): "All integrity checks passed. Proceeding.",
    (OracleDecision.ALLOW, OracleSeverity.ADVISORY): "Proceeding with advisory notice.",
    (OracleDecision.DEFER, OracleSeverity.ADVISORY): "Action deferred — integrity warnings require review.",
    (OracleDecision.DENY, OracleSeverity.CRITICAL): "Action denied — critical integrity violation detected.",
    (OracleDecision.DENY, OracleSeverity.CONSTITUTIONAL): "Action constitutionally prohibited — never-event screen triggered.",
    (OracleDecision.ESCALATE, OracleSeverity.ADVISORY): "Escalating to founder — integrity loop detected.",
    (OracleDecision.ESCALATE, OracleSeverity.CRITICAL): "Escalating to founder — critical breach requires human decision.",
}


def translate(decision: OracleDecision, severity: OracleSeverity) -> str:
    return _TRANSLATIONS.get(
        (decision, severity),
        f"Oracle decision: {decision.value} / {severity.value}.",
    )
