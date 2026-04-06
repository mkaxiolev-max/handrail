"""Authorization policy — risk tier gating."""
from shared.models.enums import RiskTier


def requires_yubikey(risk_tier: RiskTier) -> bool:
    return risk_tier in (RiskTier.R3, RiskTier.R4)


def is_founder_only(op: str) -> bool:
    FOUNDER_OPS = {
        "gov.record_decision",
        "gov.issue_constraint",
        "knowledge.promote_to_canon",
        "ma.close_transaction",
    }
    return op in FOUNDER_OPS
