"""Oracle v2 service — public entry point (C6).

Tag: oracle-v2-adjudicator-v2
"""
from __future__ import annotations

from ns.api.schemas.oracle import OracleAdjudicationRequest, OracleAdjudicationResponse
from ns.services.oracle.adjudicator import adjudicate


def evaluate(req: OracleAdjudicationRequest) -> OracleAdjudicationResponse:
    return adjudicate(req)
