from enum import Enum
from typing import Dict, Any
class RiskTier(Enum):
    R1 = {"max_retry": 3, "timeout_ms": 5000, "require_ledger": True, "require_audit": True}
    R2 = {"max_retry": 2, "timeout_ms": 10000, "require_ledger": True, "require_audit": True}
    R3 = {"max_retry": 1, "timeout_ms": 30000, "require_ledger": True, "require_audit": False}
    R4 = {"max_retry": 0, "timeout_ms": 60000, "require_ledger": False, "require_audit": False}
class RiskTierEnforcer:
    def __init__(self):
        self.tiers = {tier.name: tier.value for tier in RiskTier}
    def validate_execution(self, rb: Dict[str, Any]) -> tuple:
        risk_tier = rb.get('risk_tier', 'R1')
        if risk_tier not in self.tiers:
            return False, f"Unknown risk tier: {risk_tier}"
        return True, risk_tier
