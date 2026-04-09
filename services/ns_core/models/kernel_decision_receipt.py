from pydantic import BaseModel
from typing import Dict, Literal, Optional


class KernelDecisionReceipt(BaseModel):
    """Records a kernel-level permission decision."""
    intent_id: str
    decision: Literal["allow", "deny", "escalate"]
    gate_results: Dict[str, bool]
    timestamp: str
    reason: str
    escalation_reason: Optional[str] = None
    requester: str
    adapter_name: str
