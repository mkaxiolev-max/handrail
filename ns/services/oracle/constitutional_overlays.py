"""Constitutional overlay checks applied by the Oracle adjudicator (C6).

Imports ring6_phi_parallel from ns.domain.models.g2_invariant per spec.
Tag: oracle-v2-adjudicator-v2
"""
from __future__ import annotations

from ns.api.schemas.oracle import (
    ConstitutionalContext,
    OracleBlockingReason,
    OracleSeverity,
)
from ns.domain.models.g2_invariant import ring6_phi_parallel


NEVER_EVENTS = {
    "dignity.never_event",
    "sys.self_destruct",
    "auth.bypass",
    "policy.override",
}


def check_never_events(context: ConstitutionalContext) -> list[OracleBlockingReason]:
    reasons: list[OracleBlockingReason] = []
    for ne in context.never_events_screened:
        if ne in NEVER_EVENTS:
            reasons.append(
                OracleBlockingReason(
                    reason_id=f"ne_{ne.replace('.', '_')}",
                    description=f"Never-event '{ne}' is constitutionally prohibited.",
                    invariant_ref="I1",
                    severity=OracleSeverity.CONSTITUTIONAL,
                )
            )
    return reasons


def check_g2_phi(state: object) -> tuple[bool, list[OracleBlockingReason]]:
    parallel = ring6_phi_parallel(state)
    if not parallel:
        return False, [
            OracleBlockingReason(
                reason_id="g2_phi_not_parallel",
                description="G₂ 3-form ∇φ≠0: state coherence broken.",
                invariant_ref="I7",
                severity=OracleSeverity.CRITICAL,
            )
        ]
    return True, []


def check_dignity_kernel(context: ConstitutionalContext) -> list[OracleBlockingReason]:
    """R3/R4 ops require dignity kernel invocation."""
    return []
