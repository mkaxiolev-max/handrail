"""ReturnBlock.v2 — universal output contract for all NS∞ endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReturnBlock(BaseModel):
    return_block_version: Literal[2] = 2
    ok: bool
    rc: int = 0
    operation: str = ""
    failure_reason: Optional[str] = None
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    checks: List[Dict[str, Any]] = Field(default_factory=list)
    state_change: Optional[Dict[str, Any]] = None
    warnings: List[str] = Field(default_factory=list)
    receipt_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=_now_iso)
    dignity_banner: Literal[
        "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED"
    ] = "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED"

    @classmethod
    def ok_block(cls, operation: str = "", **kwargs) -> "ReturnBlock":
        return cls(ok=True, rc=0, operation=operation, **kwargs)

    @classmethod
    def fail_block(
        cls,
        failure_reason: str,
        rc: int = 1,
        operation: str = "",
        **kwargs,
    ) -> "ReturnBlock":
        return cls(ok=False, rc=rc, operation=operation, failure_reason=failure_reason, **kwargs)
