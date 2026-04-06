from typing import Any, Optional
from datetime import datetime
from .base import StrictModel, utc_now
from .enums import ProgramState, ProgramNamespace, RiskTier


class ProgramSummary(StrictModel):
    id: str
    namespace: ProgramNamespace
    name: str
    state: ProgramState = ProgramState.DRAFT
    description: str = ""
    ops_count: int = 0
    instance_count: int = 0
    last_activity: Optional[datetime] = None


class ProgramInstance(StrictModel):
    instance_id: str
    program_id: str
    namespace: ProgramNamespace
    state: ProgramState = ProgramState.DRAFT
    data: dict[str, Any] = {}
    receipts: list[str] = []
    created_at: datetime = None
    updated_at: datetime = None

    def model_post_init(self, __context):
        now = utc_now()
        if self.created_at is None:
            object.__setattr__(self, "created_at", now)
        if self.updated_at is None:
            object.__setattr__(self, "updated_at", now)


class TransitionProposal(StrictModel):
    program_id: str
    from_state: ProgramState
    to_state: ProgramState
    rationale: str
    risk_tier: RiskTier = RiskTier.R0
    approval_ref: Optional[str] = None


class BindingVerification(StrictModel):
    program_id: str
    instance_id: str
    binding_key: str
    verified: bool = False
    receipt_id: Optional[str] = None
