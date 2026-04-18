"""Builds audit trace list for OracleAdjudicationResponse (C6).

Tag: oracle-v2-adjudicator-v2
"""
from __future__ import annotations

from ns.api.schemas.oracle import (
    OracleBlockingReason,
    OracleCondition,
    OracleDecision,
    OracleSeverity,
)


def build_trace(
    request_id: str,
    conditions: list[OracleCondition],
    blocking_reasons: list[OracleBlockingReason],
    decision: OracleDecision,
    severity: OracleSeverity,
    g2_parallel: bool,
) -> list[str]:
    trace: list[str] = [
        f"oracle.adjudicate request_id={request_id}",
        f"g2_phi_parallel={g2_parallel}",
        f"conditions_evaluated={len(conditions)}",
        f"blocking_reasons={len(blocking_reasons)}",
    ]
    for c in conditions:
        trace.append(f"condition:{c.condition_id}:satisfied={c.satisfied}")
    for r in blocking_reasons:
        trace.append(f"blocking:{r.reason_id}:{r.severity.value}")
    trace.append(f"decision={decision.value} severity={severity.value}")
    return trace
