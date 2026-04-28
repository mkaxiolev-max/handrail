"""Coherence Kernel — canonical Pydantic v2 schemas. Strict, immutable, hash-chainable."""
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field, model_validator, computed_field

_WEIGHTS = {
    "coherence": 0.15,
    "diversity": 0.10,
    "interference_quality": 0.15,
    "evidence_weight": 0.15,
    "contradiction_metabolism": 0.10,
    "decoherence_resistance": 0.10,
    "readout_discipline": 0.10,
    "receipt_integrity": 0.10,
    "reversibility": 0.05,
}


class AmplitudeEvidenceWeight(BaseModel):
    model_config = {"frozen": True}

    magnitude: float = Field(..., ge=0.0, le=1.0)
    phase: float = Field(..., ge=-1.0, le=1.0)
    provenance_chain: list[str]
    redundancy_count: int = Field(..., ge=0)
    source_diversity: float = Field(..., ge=0.0, le=1.0)


class BranchState(BaseModel):
    model_config = {"frozen": True}

    id: str
    claim: str
    evidence_amplitude: AmplitudeEvidenceWeight
    uncertainty: float = Field(..., ge=0.0, le=1.0)
    contradiction_links: list[str] = Field(default_factory=list)
    reinforcement_links: list[str] = Field(default_factory=list)
    reversibility_cost: float = Field(..., ge=0.0)
    provenance: list[str] = Field(default_factory=list)
    parent_branch: str | None = None
    decoherence_resistance: float = Field(..., ge=0.0, le=1.0)
    qot_state_snapshot: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cps_op_chain: list[str] = Field(default_factory=list)

    def canonical_hash(self) -> str:
        payload = self.model_dump(mode="json")
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


class InterferencePass(BaseModel):
    model_config = {"frozen": True}

    input_branches: list[str]
    comparison_ops: list[str]
    cancellation_rule: str
    reinforcement_rule: str
    output_branches: list[str]
    interference_quality_score: float = Field(..., ge=0.0, le=1.0)
    receipt: str


class DecoherenceDetector(BaseModel):
    model_config = {"frozen": True}

    urgency_score: float = Field(..., ge=0.0, le=1.0)
    bias_score: float = Field(..., ge=0.0, le=1.0)
    context_loss_score: float = Field(..., ge=0.0, le=1.0)
    narrative_lock_score: float = Field(..., ge=0.0, le=1.0)
    social_pressure_score: float = Field(..., ge=0.0, le=1.0)
    aggregate: float = Field(..., ge=0.0, le=1.0)
    threshold: float = 0.65
    breached: bool

    @model_validator(mode="after")
    def _validate_breached(self) -> "DecoherenceDetector":
        expected = self.aggregate >= self.threshold
        if self.breached != expected:
            object.__setattr__(self, "breached", expected)
        return self


class CollapseReadinessScore(BaseModel):
    model_config = {"frozen": True}

    coherence: float = Field(..., ge=0.0, le=10.0)
    diversity: float = Field(..., ge=0.0, le=10.0)
    interference_quality: float = Field(..., ge=0.0, le=10.0)
    evidence_weight: float = Field(..., ge=0.0, le=10.0)
    contradiction_metabolism: float = Field(..., ge=0.0, le=10.0)
    decoherence_resistance: float = Field(..., ge=0.0, le=10.0)
    readout_discipline: float = Field(..., ge=0.0, le=10.0)
    receipt_integrity: float = Field(..., ge=0.0, le=10.0)
    reversibility: float = Field(..., ge=0.0, le=10.0)
    score_100: float = Field(..., ge=0.0, le=100.0)
    target_threshold: float = 78.0
    omega_target: float = 95.0

    @model_validator(mode="after")
    def _validate_score(self) -> "CollapseReadinessScore":
        computed = sum(
            getattr(self, k) * w * 10.0
            for k, w in _WEIGHTS.items()
        )
        if abs(computed - self.score_100) > 0.01:
            object.__setattr__(self, "score_100", round(computed, 4))
        return self

    @classmethod
    def compute(cls, **sub_metrics: float) -> "CollapseReadinessScore":
        score = sum(sub_metrics[k] * w * 10.0 for k, w in _WEIGHTS.items())
        return cls(score_100=round(score, 4), **sub_metrics)


class PointerStatePromotion(BaseModel):
    model_config = {"frozen": True}

    branch_id: str
    gate_decision: Literal["collapse_ready", "hold_ncom", "force_more_branches", "abort"]
    invariants_passed: list[str]
    invariants_advisory: list[str]
    imo_receipt: str
    root_ledger_entry: str | None = None
    reversibility_horizon_seconds: int = Field(..., ge=0)


class ReversibilityLedger(BaseModel):
    model_config = {"frozen": True}

    promotion_id: str
    rollback_cost: float = Field(..., ge=0.0)
    undo_path: str
    time_horizon_seconds: int = Field(..., ge=0)
    auditor_chamber: str
