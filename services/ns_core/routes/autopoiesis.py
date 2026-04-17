"""Autopoiesis routes — GET /autopoiesis/state, POST /autopoiesis/adapt."""
import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter

from autopoiesis.runtime import ProgramRuntime
from autopoiesis.self_loop import self_adapt, AdaptationProposal

router = APIRouter(tags=["autopoiesis"])
_runtime = ProgramRuntime()


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


@router.get("/autopoiesis/state")
async def autopoiesis_state():
    return _rb(True, "autopoiesis.state", artifacts=[_runtime.summary()])


@router.post("/autopoiesis/adapt")
async def autopoiesis_adapt(body: dict):
    proposal_data = body.get("proposal", body)
    op = proposal_data.get("op", "unknown")
    evidence = proposal_data.get("evidence", "__present__")
    proposal = AdaptationProposal(
        op=op,
        data={k: v for k, v in proposal_data.items() if k not in ("op", "evidence")},
        evidence=evidence,
    )
    result = await self_adapt(proposal, runtime=_runtime)
    return result
