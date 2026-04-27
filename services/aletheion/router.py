"""Aletheion v2.0 FastAPI router."""
from fastapi import APIRouter
from typing import Dict, Any
from datetime import datetime, timezone

from .logos_gate import logos_gate, LogosConstraintCheck
from .canon_readiness import assess_canon_readiness, CanonReadinessRequest
from .pre_action import pre_action_check

router = APIRouter(prefix="/aletheion", tags=["aletheion"])


@router.get("/healthz")
def healthz() -> Dict[str, Any]:
    return {
        "ok": True,
        "service": "aletheion",
        "version": "2.0",
        "ts": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/logos-gate")
def logos_gate_endpoint(body: Dict[str, Any]) -> Dict[str, Any]:
    check = LogosConstraintCheck(**body)
    result = logos_gate(check)
    return {"decision": result.decision, "reasons": result.reasons,
            "receipt_id": result.receipt_id}


@router.post("/canon-gate")
def canon_gate_endpoint(body: Dict[str, Any]) -> Dict[str, Any]:
    req = CanonReadinessRequest(**body)
    resp = assess_canon_readiness(req)
    return {"decision": resp.decision, "score": resp.canon_readiness_score,
            "reasons": resp.reasons}
