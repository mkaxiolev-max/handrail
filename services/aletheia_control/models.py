"""Pydantic v2 schemas for Aletheia-Control Ω."""
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, computed_field


class ControlCircle(str, Enum):
    CONTROL   = "CONTROL"
    INFLUENCE = "INFLUENCE"
    CONCERN   = "CONCERN"
    MIXED     = "MIXED"


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class ControlInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    input_id:      str   = Field(pattern=r"^inp_[a-z0-9]{6,}$")
    text:          str   = Field(min_length=1, max_length=4096)
    source:        str
    urgency:       float = Field(ge=0.0, le=1.0)
    reversibility: float = Field(ge=0.0, le=1.0)
    actor:         str   = "self"
    received_at:   datetime = Field(default_factory=_utcnow)


class ControlClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    input_id:            str
    circle:              ControlCircle
    control_weight:      float = Field(ge=0.0, le=1.0)
    influence_weight:    float = Field(ge=0.0, le=1.0)
    concern_weight:      float = Field(ge=0.0, le=1.0)
    rationale:           str
    actuator_exists:     bool
    feedback_observable: bool
    recommended_action:  str

    @model_validator(mode="after")
    def _weights_sum_to_one(self) -> "ControlClassification":
        s = self.control_weight + self.influence_weight + self.concern_weight
        if abs(s - 1.0) > 1e-3:
            raise ValueError(f"weights must sum to 1.0, got {s:.4f}")
        return self


class ControlAtom(BaseModel):
    model_config = ConfigDict(extra="forbid")
    atom_id:          str = Field(pattern=r"^atm_[a-z0-9]{6,}$")
    input_id:         str
    actor:            str
    verb:             str
    target:           str
    constraints:      Dict[str, Any] = Field(default_factory=dict)
    expected_receipt: str


class InfluenceChain(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chain_id:            str = Field(pattern=r"^chn_[a-z0-9]{6,}$")
    input_id:            str
    target_agent:        str
    influence_action:    str
    expected_conversion: float = Field(ge=0.0, le=1.0)
    conversion_deadline: datetime


class ConcernWasteRoute(BaseModel):
    model_config = ConfigDict(extra="forbid")
    waste_id:                  str = Field(pattern=r"^wst_[a-z0-9]{6,}$")
    input_id:                  str
    reason:                    str
    reingestion_cooldown_until:datetime
    archived_to:               str


class AletheiaControlReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")
    receipt_id:     str = Field(pattern=r"^rcp_[a-z0-9]{8,}$")
    timestamp:      datetime = Field(default_factory=_utcnow)
    input_id:       str
    classification: Optional[ControlClassification] = None
    control_atom:   Optional[ControlAtom]           = None
    influence_chain:Optional[InfluenceChain]        = None
    waste_route:    Optional[ConcernWasteRoute]     = None
    outcome:        str = "pending"
    score_snapshot: Dict[str, float] = Field(default_factory=dict)
    prev_hash:      str = "0"*64

    @computed_field
    @property
    def has_action(self) -> bool:
        return self.control_atom is not None or self.influence_chain is not None
