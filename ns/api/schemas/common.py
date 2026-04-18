"""Common API schemas shared across RIL + Oracle layers (C2).

Tag: ril-models-v2
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class IntegrityRouteEffect(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"


class RouteIntent(str, Enum):
    OBSERVE = "OBSERVE"
    COMMIT = "COMMIT"
    CORRECT = "CORRECT"
    ESCALATE = "ESCALATE"


class ReflexiveIntegrityState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    engine_id: str
    score: float
    effect: IntegrityRouteEffect
    tick: int = 0


class IntegritySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    aggregate_score: float
    route_effect: IntegrityRouteEffect
    engines_evaluated: int
    tick: int = 0
