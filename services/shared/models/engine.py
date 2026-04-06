from typing import Any, Optional
from datetime import datetime
from .base import StrictModel, utc_now
from .enums import OpDecision, RiskTier, IntentClass


class OpResult(StrictModel):
    op_index: int
    op: str
    args: dict[str, Any] = {}
    ok: bool
    data: Optional[Any] = None
    signal: Optional[str] = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    decision_code: OpDecision = OpDecision.OK
    op_digest: Optional[str] = None
    op_hash: Optional[str] = None
    side_effect_class: str = "read"
    validity_checked: bool = True


class IntentExecution(StrictModel):
    run_id: str
    intent: str
    keyword: str
    intent_class: IntentClass = IntentClass.DEFAULT
    ops_executed: int
    ops_passed: int
    results: list[OpResult] = []
    receipt_ref: Optional[str] = None
    next: str = "observe"
    timestamp: datetime = None

    def model_post_init(self, __context):
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", utc_now())


class DisputeRecord(StrictModel):
    dispute_id: str
    intent_run_id: str
    reason: str
    risk_tier: RiskTier = RiskTier.R0
    resolved: bool = False
    resolution: Optional[str] = None
    timestamp: datetime = None

    def model_post_init(self, __context):
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", utc_now())


class ReplayRequest(StrictModel):
    receipt_id: str
    dry_run: bool = True


class SimulateRequest(StrictModel):
    ops: list[dict[str, Any]]
    context: dict[str, Any] = {}
    dry_run: bool = True
