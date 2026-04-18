"""RIL router — POST /ril/evaluate (C8).

Tag: ril-oracle-bridge-v2
"""
from __future__ import annotations

from fastapi import APIRouter

from ns.api.schemas.ril import RILEvaluateRequest, RILEvaluateResponse
from ns.services.ril import service as ril_service

router = APIRouter(prefix="/ril", tags=["ril"])


@router.post("/evaluate", response_model=RILEvaluateResponse)
def evaluate(req: RILEvaluateRequest) -> RILEvaluateResponse:
    result, summary, route_intent = ril_service.evaluate(
        tick=req.tick,
        drift_signals=req.drift_signals,
        grounding_observations=req.grounding_observations,
        recursion_depth=req.recursion_depth,
    )
    return RILEvaluateResponse(
        result=result,
        summary=summary,
        route_intent=route_intent,
        receipts_emitted=["ril_evaluation_complete"],
    )
