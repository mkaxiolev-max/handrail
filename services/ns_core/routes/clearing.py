"""GET /clearing/recent_abstentions — Clearing Layer state endpoint."""
import uuid
from datetime import datetime, timezone
from collections import deque

from fastapi import APIRouter

router = APIRouter(tags=["clearing"])

_ABSTENTION_LOG: deque = deque(maxlen=100)


def record_abstention(reason: str, candidate_op: str = ""):
    _ABSTENTION_LOG.appendleft({
        "reason": reason,
        "op": candidate_op,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


def _rb(ok: bool, op: str, **extra):
    return {
        "return_block_version": 2,
        "ok": ok,
        "rc": 0 if ok else 1,
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


@router.get("/clearing/recent_abstentions")
async def recent_abstentions(limit: int = 20):
    return _rb(True, "clearing.recent_abstentions",
               artifacts=list(_ABSTENTION_LOG)[:limit])
