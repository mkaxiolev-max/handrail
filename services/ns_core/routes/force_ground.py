"""POST /cps/force_ground/invoke — force_ground lane endpoint."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter

from cps.lanes.force_ground import ForceGroundLane

router = APIRouter(tags=["cps"])
_lane = ForceGroundLane()


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


@router.post("/cps/force_ground/invoke")
async def force_ground_invoke(body: dict):
    ner_rate = float(body.get("ner_rate", 0.0))
    result = _lane.activate(ner_rate)
    return _rb(True, "cps.force_ground.invoke", artifacts=[result])


@router.get("/cps/force_ground/state")
async def force_ground_state():
    return _rb(True, "cps.force_ground.state", artifacts=[_lane.state()])
