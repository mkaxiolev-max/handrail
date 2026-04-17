"""KernelDecisionReceipt.v1 — stub, hardware_signed=false until YK slot_2."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class KernelDecisionReceipt(BaseModel):
    receipt_version: Literal[1] = 1
    decision_id: str
    kernel_layer: Literal["L0_genesis", "L1_protocol", "L2_canon"]
    verdict: Literal["allow", "deny", "escalate"]
    axiom_refs: List[str] = Field(default_factory=list)
    never_event_triggered: Optional[str] = None
    timestamp: str = Field(default_factory=_now_iso)
    hardware_signed: bool = False  # false until YK slot_2 bound
    dignity_banner: Literal[
        "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED"
    ] = "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED"
