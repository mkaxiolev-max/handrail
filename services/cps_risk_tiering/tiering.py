"""CPS L0–L4 risk tiering — safeguards per tier."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum


class RiskTier(IntEnum):
    L0 = 0  # no risk
    L1 = 1  # low
    L2 = 2  # moderate
    L3 = 3  # high — yubikey required
    L4 = 4  # critical — quorum required


TIER_SAFEGUARDS: dict[RiskTier, list[str]] = {
    RiskTier.L0: [],
    RiskTier.L1: ["audit_log"],
    RiskTier.L2: ["audit_log", "rate_limit"],
    RiskTier.L3: ["audit_log", "rate_limit", "yubikey_verify"],
    RiskTier.L4: ["audit_log", "rate_limit", "yubikey_verify", "quorum_2of3"],
}

DOMAIN_TIER_MAP: dict[str, RiskTier] = {
    "fs": RiskTier.L1,
    "git": RiskTier.L2,
    "proc": RiskTier.L2,
    "docker": RiskTier.L2,
    "http": RiskTier.L1,
    "sys": RiskTier.L1,
    "slack": RiskTier.L1,
    "email": RiskTier.L1,
    "stripe": RiskTier.L3,
    "schedule": RiskTier.L2,
    "ns": RiskTier.L2,
    "gov": RiskTier.L4,
    "ma": RiskTier.L4,
    "auth": RiskTier.L3,
}


@dataclass
class TierAssessment:
    op: str
    domain: str
    tier: RiskTier
    safeguards: list[str]
    yubikey_required: bool
    quorum_required: bool


def classify_op(op: str) -> TierAssessment:
    domain = op.split(".")[0] if "." in op else op
    tier = DOMAIN_TIER_MAP.get(domain, RiskTier.L1)
    safeguards = TIER_SAFEGUARDS[tier]
    return TierAssessment(
        op=op,
        domain=domain,
        tier=tier,
        safeguards=safeguards,
        yubikey_required=tier >= RiskTier.L3,
        quorum_required=tier >= RiskTier.L4,
    )


def required_safeguards(tier: RiskTier) -> list[str]:
    return list(TIER_SAFEGUARDS[tier])


def tier_from_int(level: int) -> RiskTier:
    return RiskTier(level)
