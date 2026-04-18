"""NS∞ integrity domain models — RIL + Oracle layer (C2).

Tag: ril-models-v2
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class ProvenanceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    hash_chain_id: Optional[str] = None
    tick: int = 0


class CanonRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str
    commit_idx: int


class IntegrityState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    canon_valid: bool = True
    lineage_valid: bool = True
    provenance_valid: bool = True


# ---------------------------------------------------------------------------
# RIL-specific models
# ---------------------------------------------------------------------------

class DriftSignal(BaseModel):
    """Detected semantic drift from Gradient Field baseline (L2)."""
    model_config = ConfigDict(extra="forbid")

    signal_id: str
    magnitude: float  # 0.0 = no drift, 1.0 = maximal
    layer: str  # e.g. "L2_gradient", "L5_lexicon"
    tick: int = 0
    suppressed: bool = False

    @field_validator("magnitude")
    @classmethod
    def magnitude_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("magnitude must be in [0.0, 1.0]")
        return v


class GroundingObservation(BaseModel):
    """Empirical anchor from Gradient Field — grounds narrative to fact (I18)."""
    model_config = ConfigDict(extra="forbid")

    observation_id: str
    content: str
    confidence: float  # 0.0-1.0
    provenance: Optional[ProvenanceRecord] = None
    tick: int = 0

    @field_validator("confidence")
    @classmethod
    def confidence_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence must be in [0.0, 1.0]")
        return v


class CommitmentRecord(BaseModel):
    """Commitment state for a proposition under evaluation."""
    model_config = ConfigDict(extra="forbid")

    commitment_id: str
    proposition: str
    committed: bool = False
    strength: float = 0.0  # 0.0-1.0
    tick: int = 0

    @field_validator("strength")
    @classmethod
    def strength_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("strength must be in [0.0, 1.0]")
        return v


class EncounterRecord(BaseModel):
    """Encounter with a contradiction or competing observation."""
    model_config = ConfigDict(extra="forbid")

    encounter_id: str
    contradiction_weight: float  # 0.0-1.0
    resolved: bool = False
    resolution_tick: Optional[int] = None

    @field_validator("contradiction_weight")
    @classmethod
    def weight_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("contradiction_weight must be in [0.0, 1.0]")
        return v


class RealityBinding(BaseModel):
    """Binding of narrative output to ≥1 verifiable Gradient Field observation (I18)."""
    model_config = ConfigDict(extra="forbid")

    binding_id: str
    observation_ids: list[str]
    is_bound: bool


class RenderingCapture(BaseModel):
    """Captured rendering output — audit trail for Narrative Interface (L10)."""
    model_config = ConfigDict(extra="forbid")

    capture_id: str
    rendered_text: str
    bound_observation_ids: list[str] = []
    tick: int = 0


class RILEngineResult(BaseModel):
    """Result emitted by a single RIL integrity engine."""
    model_config = ConfigDict(extra="forbid")

    engine_id: str
    score: float  # 0.0-1.0; higher = healthier
    passed: bool
    detail: Optional[str] = None
    tick: int = 0

    @field_validator("score")
    @classmethod
    def score_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("score must be in [0.0, 1.0]")
        return v


class RILEvaluationResult(BaseModel):
    """Aggregate result across all RIL integrity engines."""
    model_config = ConfigDict(extra="forbid")

    aggregate_score: float  # 0.0-1.0
    engine_results: list[RILEngineResult]
    all_passed: bool
    tick: int = 0

    @field_validator("aggregate_score")
    @classmethod
    def score_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("aggregate_score must be in [0.0, 1.0]")
        return v
