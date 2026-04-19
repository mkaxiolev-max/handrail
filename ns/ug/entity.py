"""
axiolev-ug-entity-v2
AXIOLEV Holdings LLC © 2026 — axiolevns@axiolev.com

Universal Entity primitive (per UG_max_ready_to_integrate_.pdf).
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class EntityKind(str, Enum):
    BRANCH = "branch"
    DELTA = "delta"
    ENTANGLEMENT = "entanglement"
    CONTRADICTION = "contradiction"
    SEMANTIC_ANCHOR = "semantic_anchor"
    SHARD_MANIFEST = "shard_manifest"
    PROJECTION = "projection"
    STORYTIME = "storytime"
    RECEIPT = "receipt"
    PROGRAM = "program"
    OTHER = "other"


class Identity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    canonical_name: str
    aliases: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)


class Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    origin: str
    chain: List[str] = Field(default_factory=list)


class Epistemics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evidence: float = Field(ge=0.0, le=1.0, default=0.5)
    contradiction: float = Field(ge=0.0, le=1.0, default=0.0)
    novelty: float = Field(ge=0.0, le=1.0, default=0.0)
    stability: float = Field(ge=0.0, le=1.0, default=1.0)


class Supersession(BaseModel):
    model_config = ConfigDict(extra="forbid")
    superseded_id: Optional[str] = None
    superseded_by_id: Optional[str] = None


class Timestamps(BaseModel):
    model_config = ConfigDict(extra="forbid")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    emitted_at: Optional[datetime] = None


class Entity(BaseModel):
    """Universal NS∞ node primitive."""
    model_config = ConfigDict(extra="forbid")
    id: str
    kind: EntityKind
    identity: Identity
    state: Dict[str, Any] = Field(default_factory=dict)
    provenance: Provenance
    epistemics: Epistemics = Field(default_factory=Epistemics)
    constraints: List[str] = Field(default_factory=list)
    relations: List[Dict[str, Any]] = Field(default_factory=list)
    manifestations: List[Dict[str, Any]] = Field(default_factory=list)
    receipts: List[str] = Field(default_factory=list)
    bindings: Dict[str, Any] = Field(default_factory=dict)
    supersession: Supersession = Field(default_factory=Supersession)
    timestamps: Timestamps = Field(default_factory=Timestamps)
    metadata: Dict[str, Any] = Field(default_factory=dict)
