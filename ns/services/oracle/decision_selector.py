"""Oracle decision selector — maps blocking reasons + RIL effect to OracleDecision (C6).

Tag: oracle-v2-adjudicator-v2
"""
from __future__ import annotations

from ns.api.schemas.common import IntegrityRouteEffect
from ns.api.schemas.oracle import OracleBlockingReason, OracleDecision, OracleSeverity


def select_decision(
    blocking_reasons: list[OracleBlockingReason],
    ril_route_effect: IntegrityRouteEffect,
) -> OracleDecision:
    if any(r.severity == OracleSeverity.CONSTITUTIONAL for r in blocking_reasons):
        return OracleDecision.DENY
    if any(r.severity == OracleSeverity.CRITICAL for r in blocking_reasons):
        return OracleDecision.DENY
    if ril_route_effect == IntegrityRouteEffect.ESCALATE:
        return OracleDecision.ESCALATE
    if ril_route_effect == IntegrityRouteEffect.BLOCK:
        return OracleDecision.DENY
    if ril_route_effect == IntegrityRouteEffect.WARN:
        return OracleDecision.DEFER
    return OracleDecision.ALLOW


def select_severity(
    blocking_reasons: list[OracleBlockingReason],
    decision: OracleDecision,
) -> OracleSeverity:
    if any(r.severity == OracleSeverity.CONSTITUTIONAL for r in blocking_reasons):
        return OracleSeverity.CONSTITUTIONAL
    if decision == OracleDecision.DENY:
        return OracleSeverity.CRITICAL
    if decision in (OracleDecision.ESCALATE, OracleDecision.DEFER):
        return OracleSeverity.ADVISORY
    return OracleSeverity.NOMINAL
