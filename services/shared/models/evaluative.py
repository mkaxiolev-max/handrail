"""EvaluativeEnvelope — 5-block wrapper for all NS∞ decisions."""
from typing import Any, Optional
from datetime import datetime
from .base import StrictModel, utc_now
from .enums import RiskTier, OpDecision


class ObservationBlock(StrictModel):
    """Block 1: What is actually happening."""
    inputs: dict[str, Any] = {}
    context_snapshot: dict[str, Any] = {}
    timestamp: datetime = None

    def model_post_init(self, __context):
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", utc_now())


class EvaluationBlock(StrictModel):
    """Block 2: What does it mean."""
    risk_tier: RiskTier = RiskTier.R0
    flags: list[str] = []
    confidence: float = 1.0
    rationale: str = ""


class DecisionBlock(StrictModel):
    """Block 3: What action to take."""
    decision: OpDecision = OpDecision.OK
    action: str = ""
    parameters: dict[str, Any] = {}
    yubikey_required: bool = False


class ExecutionBlock(StrictModel):
    """Block 4: What happened."""
    executed: bool = False
    result: Optional[Any] = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    side_effects: list[str] = []


class ReceiptBlock(StrictModel):
    """Block 5: Immutable proof of execution."""
    receipt_id: str = ""
    op_digest: str = ""
    ledger_hash: str = ""
    timestamp: datetime = None

    def model_post_init(self, __context):
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", utc_now())


class EvaluativeEnvelope(StrictModel):
    """Full 5-block evaluative wrapper for all NS∞ decisions."""
    envelope_id: str
    observation: ObservationBlock = ObservationBlock()
    evaluation: EvaluationBlock = EvaluationBlock()
    decision: DecisionBlock = DecisionBlock()
    execution: ExecutionBlock = ExecutionBlock()
    receipt: ReceiptBlock = ReceiptBlock()
