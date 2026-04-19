"""
axiolev-omega-primitives-v2
AXIOLEV Holdings LLC © 2026 — axiolevns@axiolev.com

Omega L10 Pydantic v2 primitives per Omega Whitepaper Section III.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class Recoverability(str, Enum):
    EXACT = "exact"
    RECONSTRUCTIBLE = "reconstructible"
    SEMANTIC_EQUIVALENT = "semantic_equivalent"
    PARTIAL = "partial"
    UNRECOVERABLE = "unrecoverable"


class ProjectionMode(str, Enum):
    HISTORICAL = "historical"
    CURRENT = "current"
    COUNTERFACTUAL = "counterfactual"
    HYPOTHETICAL = "hypothetical"
    PROPOSED = "proposed"
    NARRATIVE = "narrative"


class RecoveryStrategy(str, Enum):
    EXACT_LOCAL = "exact_local"
    DELTA_REPLAY = "delta_replay"
    SHARD_RECOVERY = "shard_recovery"
    ENTANGLEMENT_ASSISTED = "entanglement_assisted"
    SEMANTIC = "semantic"
    GRACEFUL_PARTIAL = "graceful_partial"


class ConfidenceEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    evidence: float = Field(ge=0.0, le=1.0)
    contradiction: float = Field(ge=0.0, le=1.0)
    novelty: float = Field(ge=0.0, le=1.0)
    stability: float = Field(ge=0.0, le=1.0)

    @property
    def score(self) -> float:
        return (
            0.45 * self.evidence
            + 0.25 * (1.0 - self.contradiction)
            + 0.15 * self.novelty
            + 0.15 * self.stability
        )


class Branch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    parent_id: Optional[str] = None
    title: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    canon_promoted: bool = False
    mode: ProjectionMode = ProjectionMode.CURRENT


class Delta(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    branch_id: str
    prev_hash: Optional[str] = None
    payload_hash: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Entanglement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    branch_ids: List[str]
    relation: str
    strength: float = Field(ge=0.0, le=1.0, default=0.5)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Contradiction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    branch_ids: List[str]
    axis: str
    severity: float = Field(ge=0.0, le=1.0)
    resolved: bool = False


class SemanticAnchor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    branch_id: str
    concept: str
    embedding_ref: Optional[str] = None


class ShardManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    branch_id: str
    shards: List[str]
    checksum: str


class ProjectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    branch_id: str
    mode: ProjectionMode
    requested_by: str
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProjectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str
    branch_id: str
    mode: ProjectionMode
    confidence: ConfidenceEnvelope
    recoverability: Recoverability
    order_used: List[RecoveryStrategy] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(default_factory=dict)
    emitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ForkOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    parent_branch_id: str
    child_branch_id: str
    rationale: str


class MergeOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    source_branch_ids: List[str]
    target_branch_id: str
    rationale: str


class SupersessionOp(BaseModel):
    """I10: supersession is monotone; old never deleted."""
    model_config = ConfigDict(extra="forbid")
    id: str
    superseded_id: str
    superseded_by_id: str
    effective_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Storytime(BaseModel):
    """L10 Narrative service. Read-only synthesis. L10 NEVER amends L1-L9."""
    model_config = ConfigDict(extra="forbid")
    id: str
    branch_id: str
    mode: ProjectionMode
    narrative: str
    confidence: ConfidenceEnvelope
    emitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
