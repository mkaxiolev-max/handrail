"""Pydantic schemas for NCOM/PIIC Founder Console endpoints (B5)."""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, ConfigDict


class NCOMStateSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: str
    history: list[str]
    is_terminal: bool
    is_collapse_ready: bool


class PIICStageSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage: str
    history: list[str]
    is_committed: bool


class CollapseReadinessSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ERS: float
    CRS: float
    IPI: float
    contradictionPressure: float
    branchDiversityAdequacy: float
    hardVetoes: list[str]
    recommendedAction: str


class FounderConsoleSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ncom: NCOMStateSnapshot
    piic: PIICStageSnapshot
    readiness: CollapseReadinessSnapshot
    timestamp: str


class HistoryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: str
    value: str
    timestamp: str


class FounderConsoleHistory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ncom_history: list[HistoryEntry]
    piic_history: list[HistoryEntry]


class ContradictionEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    description: str
    weight: float
    source: Optional[str] = None


class ContradictionList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    active: list[ContradictionEntry]
    count: int


class ObservationEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    content: str
    stage: str
    open: bool


class ObservationList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    open: list[ObservationEntry]
    count: int


class RoutingCurrent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    active_layer: str
    top_interpretation: Optional[str] = None
    route_intent: Optional[str] = None
    metadata: dict[str, Any] = {}


class ReceiptEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    receipt_name: str
    timestamp: str
    payload: dict[str, Any] = {}


class ReceiptList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recent: list[ReceiptEntry]
    count: int
