"""Omega L10 Projection/Ego Layer — Pydantic v2 primitives.

Ontology (locked — do NOT reintroduce deprecated names):
  L5 Alexandrian Lexicon | L6 State Manifold | L7 Alexandrian Archive
  L8 Lineage Fabric | L10 Narrative + Interface (Omega + Violet)

Invariants: I1 Canon precedes Conversion, I2/I5/I10 append-only hash-chained.
AXIOLEV Holdings LLC © 2026
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


class Recoverability(str, Enum):
    EXACT = "exact"
    LOSSLESS_STRUCTURAL = "lossless_structural"
    LOSSLESS_SEMANTIC = "lossless_semantic"
    LOSSY_SEMANTIC = "lossy_semantic"
    IRRECOVERABLE = "irrecoverable"


class ProjectionMode(str, Enum):
    EXACT_VIEW = "exact_view"
    BRANCH_VIEW = "branch_view"
    MERGED_VIEW = "merged_view"
    CANON_VIEW = "canon_view"
    PARTIAL_RECONSTRUCTION = "partial_reconstruction"
    CONTRASTIVE_VIEW = "contrastive_view"


class ConfidenceEnvelope(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    evidence: float = Field(ge=0.0, le=1.0)
    contradiction: float = Field(ge=0.0, le=1.0)
    novelty: float = Field(ge=0.0, le=1.0)
    stability: float = Field(ge=0.0, le=1.0)

    def score(self) -> float:
        # Locked constitutional weights — amendment requires
        # HIC + PDP + YubiKey quorum (see Ring 4).
        return (0.45 * self.evidence
                + 0.25 * (1.0 - self.contradiction)
                + 0.15 * self.novelty
                + 0.15 * self.stability)


class Branch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    parent_id: Optional[str] = None
    created_at: datetime = Field(default_factory=_now)
    title: str
    lineage: list[str] = Field(default_factory=list)
    canon: bool = False


class Delta(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    id: str
    branch_id: str
    seq: int = Field(ge=0)
    op: Literal["add", "amend", "retract", "supersede"]
    payload: dict
    prev_hash: str
    hash: str
    author: str
    ts: datetime = Field(default_factory=_now)


class Entanglement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    a_ref: str
    b_ref: str
    kind: Literal["coref", "causal", "contradiction_coupling", "semantic_shadow"]
    weight: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class Contradiction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    claim_a: str
    claim_b: str
    pressure: float = Field(ge=0.0, le=1.0)
    resolution: Literal[
        "open", "superseded", "branch_split", "accepted_paraconsistent"
    ] = "open"
    resolution_ref: Optional[str] = None


class SemanticAnchor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    label: str
    embedding_ref: str
    recoverability: Recoverability = Recoverability.LOSSLESS_SEMANTIC
    stability: float = Field(ge=0.0, le=1.0, default=1.0)


class ShardManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    shards: list[str]
    erasure_scheme: str = "rs(10,4)"
    merkle_root: str
    recoverability: Recoverability = Recoverability.LOSSLESS_STRUCTURAL


class ProjectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_ref: str
    mode: ProjectionMode
    constraints: dict = Field(default_factory=dict)
    requested_by: str


class ProjectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_ref: str
    mode: ProjectionMode
    content: dict
    order_used: list[str]
    confidence: ConfidenceEnvelope
    recoverability: Recoverability
    lineage: list[str]
    ts: datetime = Field(default_factory=_now)


class ForkOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    from_branch: str
    to_branch: str
    reason: str
    authorizer: str
    pdp_decision_ref: str
    hic_approval_ref: Optional[str] = None
    ts: datetime = Field(default_factory=_now)


class MergeOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    branches: list[str]
    into: str
    policy: str
    authorizer: str
    pdp_decision_ref: str
    hic_approval_ref: str
    ts: datetime = Field(default_factory=_now)


class SupersessionOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    superseded_ref: str
    superseder_ref: str
    reason: str
    authorizer: str
    pdp_decision_ref: str
    hic_approval_ref: str
    ts: datetime = Field(default_factory=_now)


class Storytime(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    projection_ref: str
    narrative: str
    arc: list[str] = Field(default_factory=list)
    ts: datetime = Field(default_factory=_now)
