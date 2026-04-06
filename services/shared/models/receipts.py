from typing import Any, Optional
from datetime import datetime
from .base import StrictModel, utc_now
from .enums import ReceiptType, RiskTier


class Receipt(StrictModel):
    receipt_id: str
    receipt_type: ReceiptType
    op: Optional[str] = None
    actor: str = "system"
    risk_tier: RiskTier = RiskTier.R0
    payload: dict[str, Any] = {}
    op_digest: Optional[str] = None
    ledger_hash: Optional[str] = None
    prev_hash: Optional[str] = None
    timestamp: datetime = None

    def model_post_init(self, __context):
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", utc_now())


class ReceiptChainStatus(StrictModel):
    total_receipts: int = 0
    latest_hash: Optional[str] = None
    latest_receipt_id: Optional[str] = None
    integrity_ok: bool = True
    last_verified: Optional[datetime] = None
