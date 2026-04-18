"""L1 Constitutional Layer — canon schemas."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ConstraintClass(str, Enum):
    SACRED = "SACRED"
    RELAXABLE = "RELAXABLE"


class ConstitutionalRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    description: str
    constraint_class: ConstraintClass
    invariant_ref: Optional[str] = None


class DignityCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str
    passed: bool
    reason: Optional[str] = None


class NeverEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    description: str
    rule_id: str
