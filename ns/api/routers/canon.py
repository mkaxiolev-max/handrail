"""Canon router — POST /canon/promote (Ring 4)."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ns.services.canon.promotion_guard import PromotionGuard
from ns.services.loom.service import ConfidenceEnvelope

router = APIRouter(prefix="/canon", tags=["canon"])


class PromoteRequest(BaseModel):
    branch_id: str
    confidence_evidence: float
    confidence_contradiction: float
    confidence_novelty: float
    confidence_stability: float
    contradiction_weight: float
    reconstructability: float
    lineage_valid: bool
    hic_approval: bool
    pdp_approval: bool
    quorum_certs: list[dict]
    state: dict = {}


class PromoteResponse(BaseModel):
    allowed: bool
    receipt_name: str
    branch_id: str


@router.post("/promote", response_model=PromoteResponse)
async def promote(request: PromoteRequest) -> PromoteResponse:
    envelope = ConfidenceEnvelope(
        evidence=request.confidence_evidence,
        contradiction=request.confidence_contradiction,
        novelty=request.confidence_novelty,
        stability=request.confidence_stability,
    )
    context = {
        "confidence": envelope,
        "contradiction_weight": request.contradiction_weight,
        "reconstructability": request.reconstructability,
        "lineage_valid": request.lineage_valid,
        "hic_approval": request.hic_approval,
        "pdp_approval": request.pdp_approval,
        "quorum_certs": request.quorum_certs,
        "state": request.state,
    }
    result = PromotionGuard().promote(request.branch_id, context)
    return PromoteResponse(
        allowed=result["allowed"],
        receipt_name=result["receipt_name"],
        branch_id=result["branch_id"],
    )
