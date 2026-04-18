"""Oracle router — POST /oracle/adjudicate (C8).

Tag: ril-oracle-bridge-v2
"""
from __future__ import annotations

from fastapi import APIRouter

from ns.api.schemas.oracle import OracleAdjudicationRequest, OracleAdjudicationResponse
from ns.services.oracle import service as oracle_service

router = APIRouter(prefix="/oracle", tags=["oracle"])


@router.post("/adjudicate", response_model=OracleAdjudicationResponse)
def adjudicate(req: OracleAdjudicationRequest) -> OracleAdjudicationResponse:
    return oracle_service.evaluate(req)
