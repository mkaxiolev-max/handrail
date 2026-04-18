"""Builds OracleCondition list from HandrailExecutionEnvelope (C6).

Tag: oracle-v2-adjudicator-v2
"""
from __future__ import annotations

from ns.api.schemas.oracle import (
    HandrailExecutionEnvelope,
    OracleCondition,
    OracleSeverity,
)

HIGH_RISK_TIERS = {"R3", "R4"}


def build_conditions(envelope: HandrailExecutionEnvelope) -> list[OracleCondition]:
    conditions: list[OracleCondition] = []

    yubikey_required = envelope.risk_tier in HIGH_RISK_TIERS
    conditions.append(
        OracleCondition(
            condition_id="yubikey_gate",
            description="YubiKey verification required for R3/R4 risk tiers.",
            satisfied=(not yubikey_required) or envelope.yubikey_verified,
            severity=OracleSeverity.CRITICAL if yubikey_required else OracleSeverity.NOMINAL,
        )
    )

    conditions.append(
        OracleCondition(
            condition_id="risk_tier_acknowledged",
            description=f"Risk tier {envelope.risk_tier} acknowledged.",
            satisfied=True,
            severity=OracleSeverity.NOMINAL,
        )
    )

    return conditions


def blocking_from_conditions(
    conditions: list[OracleCondition],
) -> list:
    """Return OracleBlockingReason for each unsatisfied CRITICAL/CONSTITUTIONAL condition."""
    from ns.api.schemas.oracle import OracleBlockingReason

    reasons = []
    for c in conditions:
        if not c.satisfied and c.severity in (OracleSeverity.CRITICAL, OracleSeverity.CONSTITUTIONAL):
            reasons.append(
                OracleBlockingReason(
                    reason_id=f"condition_fail_{c.condition_id}",
                    description=c.description,
                    severity=c.severity,
                )
            )
    return reasons
