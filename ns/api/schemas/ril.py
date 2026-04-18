"""Pydantic schemas for RIL API endpoints (C2).

Tag: ril-models-v2
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from ns.api.schemas.common import IntegritySummary, RouteIntent
from ns.domain.models.integrity import (
    DriftSignal,
    GroundingObservation,
    RILEvaluationResult,
)


class RILEvaluateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tick: int = 0
    context: dict[str, Any] = {}
    drift_signals: list[DriftSignal] = []
    grounding_observations: list[GroundingObservation] = []
    recursion_depth: int = 0


class RILEvaluateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result: RILEvaluationResult
    summary: IntegritySummary
    route_intent: RouteIntent
    receipts_emitted: list[str] = []
