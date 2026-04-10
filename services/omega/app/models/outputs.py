from typing import Any, Literal

from pydantic import Field

from app.models.inputs import OmegaStrictModel


class OmegaConfidenceGeometry(OmegaStrictModel):
    evidence_depth: float = Field(default=0.0, ge=0.0, le=1.0)
    observability: float = Field(default=0.0, ge=0.0, le=1.0)
    branch_stability: float = Field(default=0.0, ge=0.0, le=1.0)
    divergence_pressure: float = Field(default=0.0, ge=0.0, le=1.0)
    model_fit: float = Field(default=0.0, ge=0.0, le=1.0)
    constraint_satisfaction: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    degraded: bool = False
    epistemic_boundary: str = "Insufficient simulation evidence yet."


class OmegaTransition(OmegaStrictModel):
    step_index: int = Field(ge=0)
    observed_state: dict[str, Any] = Field(default_factory=dict)
    inferred_state: dict[str, Any] = Field(default_factory=dict)
    delta: dict[str, float] = Field(default_factory=dict)
    constraint_pressure: float = Field(default=0.0, ge=0.0, le=1.0)
    notes: list[str] = Field(default_factory=list)


class OmegaBreachPoint(OmegaStrictModel):
    step_index: int = Field(ge=0)
    variable: str
    trigger: str
    severity: float = Field(default=0.0, ge=0.0, le=1.0)
    description: str


class OmegaInterventionCandidate(OmegaStrictModel):
    step_index: int = Field(ge=0)
    variable: str
    action: str
    expected_effect: str
    leverage_score: float = Field(default=0.0, ge=0.0, le=1.0)


class OmegaBranch(OmegaStrictModel):
    branch_id: str
    parent_run_id: str
    branch_index: int = Field(ge=0)
    assumptions: list[str] = Field(default_factory=list)
    transitions: list[OmegaTransition] = Field(default_factory=list)
    outputs: dict[str, Any] = Field(default_factory=dict)
    likelihood: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: OmegaConfidenceGeometry = Field(default_factory=OmegaConfidenceGeometry)
    breach_points: list[OmegaBreachPoint] = Field(default_factory=list)
    divergence_components: dict[str, float] = Field(default_factory=dict)
    provisional: Literal[True] = True


class OmegaSummary(OmegaStrictModel):
    most_likely_branch: str | None = None
    branch_spread: dict[str, float] = Field(default_factory=dict)
    divergence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_geometry: OmegaConfidenceGeometry = Field(default_factory=OmegaConfidenceGeometry)
    key_branch_points: list[OmegaBreachPoint] = Field(default_factory=list)
    intervention_candidates: list[OmegaInterventionCandidate] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    epistemic_boundary: str = "Simulation remains provisional and non-canonical."


class OmegaFounderEnvelope(OmegaStrictModel):
    status: str
    run_id: str
    receipt_hash: str
    chain_verified: bool
    provisional: Literal[True] = True
    simulation_class: str = "bounded_causal_simulation"
    divergence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: OmegaConfidenceGeometry = Field(default_factory=OmegaConfidenceGeometry)
    warnings: list[str] = Field(default_factory=list)
    summary: OmegaSummary = Field(default_factory=OmegaSummary)
    branches: list[OmegaBranch] = Field(default_factory=list)
    memory_atoms_written: int = 0
    canon_version: int | None = None
    result_kind: Literal["simulation"] = "simulation"
    # Policy contract — carried on every response
    policy_state: str = "advisory_only"
    promotion_allowed: bool = False
    execution_allowed: bool = False
