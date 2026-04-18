"""Oracle v2 policy matrix — op-domain risk classification (C7).

Tag: oracle-policy-matrix-v2
"""
from __future__ import annotations

from ns.api.schemas.oracle import OracleSeverity

# Domains that always require elevated scrutiny
HIGH_RISK_DOMAINS = {"auth", "policy", "sys", "gov", "ma"}

# Ops that are always constitutional never-events (mapped to DENY)
NEVER_EVENT_OPS = {
    "dignity.never_event",
    "sys.self_destruct",
    "auth.bypass",
    "policy.override",
}

# Risk-tier to severity mapping
TIER_SEVERITY: dict[str, OracleSeverity] = {
    "R0": OracleSeverity.NOMINAL,
    "R1": OracleSeverity.NOMINAL,
    "R2": OracleSeverity.ADVISORY,
    "R3": OracleSeverity.CRITICAL,
    "R4": OracleSeverity.CONSTITUTIONAL,
}


def op_severity(op_domain: str | None, op_name: str | None, risk_tier: str) -> OracleSeverity:
    """Return the policy-matrix severity for an op."""
    fq = f"{op_domain}.{op_name}" if op_domain and op_name else ""
    if fq in NEVER_EVENT_OPS:
        return OracleSeverity.CONSTITUTIONAL
    tier_sev = TIER_SEVERITY.get(risk_tier, OracleSeverity.ADVISORY)
    if op_domain in HIGH_RISK_DOMAINS and tier_sev == OracleSeverity.NOMINAL:
        return OracleSeverity.ADVISORY
    return tier_sev


def is_never_event(op_domain: str | None, op_name: str | None) -> bool:
    fq = f"{op_domain}.{op_name}" if op_domain and op_name else ""
    return fq in NEVER_EVENT_OPS
