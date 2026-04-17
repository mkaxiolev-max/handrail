"""Self-loop — every adaptation calls /pi/check BEFORE mutating anything.

ABSOLUTE PRECONDITION: never adapt without pi_check accept.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from pi.engine import PiEngine, PiCheckRequest

_pi = PiEngine()


class AdaptationProposal:
    def __init__(self, op: str, data: Dict[str, Any] = None, evidence: Any = "__present__"):
        self.op = op
        self.data = data or {}
        self.evidence = evidence

    def to_dict(self) -> Dict[str, Any]:
        return {"op": self.op, "evidence": self.evidence, **self.data}


def _rb(ok: bool, rc: int, op: str, **extra) -> Dict[str, Any]:
    return {
        "return_block_version": 2,
        "ok": ok,
        "rc": rc,
        "operation": op,
        "failure_reason": None,
        "artifacts": [],
        "checks": [],
        "state_change": None,
        "warnings": [],
        "receipt_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dignity_banner": "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED",
        **extra,
    }


async def self_adapt(
    proposal: AdaptationProposal,
    runtime=None,
) -> Dict[str, Any]:
    """Gate: pi_check MUST accept before any mutation."""
    pi_result = _pi.check(PiCheckRequest(candidate=proposal.to_dict()))

    if not pi_result.admissible or pi_result.abstention:
        return _rb(
            False, 1, "autopoiesis.self_adapt",
            failure_reason="pi_blocked",
            checks=[pi_result.model_dump()],
        )

    record = {}
    if runtime is not None:
        record = runtime.record_adaptation(proposal.to_dict())

    return _rb(
        True, 0, "autopoiesis.self_adapt",
        artifacts=[{"adaptation": proposal.to_dict(), "record": record}],
        checks=[pi_result.model_dump()],
    )
