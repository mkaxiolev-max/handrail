"""NS∞ CQHML Manifold Engine — dimensional schemas (E2).

Tag: cqhml-dimensions-v2
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SemanticMode(str, Enum):
    GRADIENT = "GRADIENT"           # L2 Gradient Field
    INTAKE = "INTAKE"               # L3 Epistemic Envelope
    CONVERSION = "CONVERSION"       # L4 The Loom
    LEXICAL = "LEXICAL"             # L5 Alexandrian Lexicon
    STATE = "STATE"                 # L6 State Manifold
    MEMORY = "MEMORY"               # L7 Alexandrian Archive
    LINEAGE = "LINEAGE"             # L8 Lineage Fabric
    NARRATIVE = "NARRATIVE"         # L10 Ω-Link Narrative Interface
    CONSTITUTIONAL = "CONSTITUTIONAL"  # L1 Constitutional
    ERROR = "ERROR"                 # L9 HIC/PDP


class PolicyMode(str, Enum):
    ENFORCE = "ENFORCE"
    ADVISORY = "ADVISORY"
    AUDIT = "AUDIT"
    CONSTITUTIONAL_BLOCK = "CONSTITUTIONAL_BLOCK"


class DimensionalCoordinate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    layer: int = Field(..., ge=1, le=10, description="L1–L10 ontology layer")
    axis: str = Field(default="canonical", description="Named axis within the layer")
    tick: int = Field(default=0, ge=0)
    phi_parallel: bool = Field(default=True, description="G₂ 3-form coherence flag")
    magnitude: float = Field(default=1.0, ge=0.0)


class ObserverFrame(BaseModel):
    model_config = ConfigDict(extra="forbid")

    frame_id: str
    layer: int = Field(..., ge=1, le=10)
    semantic_mode: SemanticMode = SemanticMode.STATE
    policy_mode: PolicyMode = PolicyMode.ENFORCE
    tick: int = Field(default=0, ge=0)
    quorum_verified: bool = False


class DimensionalEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    coordinate: DimensionalCoordinate
    observer: ObserverFrame
    g2_phi_parallel: bool = True
    spin7_coherent: bool = True
    tick: int = Field(default=0, ge=0)
    receipts_attached: list[str] = []


class ProjectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    envelope: DimensionalEnvelope
    target_layer: int = Field(..., ge=1, le=10)
    semantic_mode: Optional[SemanticMode] = None
    policy_mode: Optional[PolicyMode] = None
    context: dict = {}
    tick: int = Field(default=0, ge=0)


class ProjectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    success: bool
    projected_coordinate: Optional[DimensionalCoordinate] = None
    source_layer: int = Field(default=1, ge=1, le=10)
    target_layer: int = Field(default=1, ge=1, le=10)
    g2_phi_parallel: bool = True
    receipts_emitted: list[str] = []
    trace: list[str] = []
    tick: int = Field(default=0, ge=0)
    error: Optional[str] = None
