from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class InfraBootReport(BaseModel):
    boot_ok: bool = False
    run_id: str
    boot_timestamp: str

    container_status: Dict[str, Any] = Field(default_factory=dict)
    endpoint_status: Dict[str, Any] = Field(default_factory=dict)
    storage_status: Dict[str, Any] = Field(default_factory=dict)
    auth_status: Dict[str, Any] = Field(default_factory=dict)
    dependency_status: Dict[str, Any] = Field(default_factory=dict)


class PresentStateKernel(BaseModel):
    mission_mode: str
    current_objective: str
    active_goals: List[str] = Field(default_factory=list)

    hard_constraints: List[str] = Field(default_factory=list)
    soft_constraints: List[str] = Field(default_factory=list)

    unresolved_commitments: List[str] = Field(default_factory=list)
    current_risks: List[str] = Field(default_factory=list)

    engine_health: Dict[str, Any] = Field(default_factory=dict)
    environment_status: Dict[str, Any] = Field(default_factory=dict)
    active_domains: List[str] = Field(default_factory=list)
    resonance_weights: Dict[str, float] = Field(default_factory=dict)

    allowed_action_bands: List[str] = Field(default_factory=list)
    operator_override_flags: Dict[str, Any] = Field(default_factory=dict)

    confidence_score: float = 0.0
    instability_score: float = 1.0
    boot_timestamp: str


class AncestryNode(BaseModel):
    node_id: str
    node_type: str
    summary: str
    source_ref: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AncestryEdge(BaseModel):
    from_node: str
    to_node: str
    edge_type: str


class AncestryGraph(BaseModel):
    run_id: str
    nodes: List[AncestryNode] = Field(default_factory=list)
    edges: List[AncestryEdge] = Field(default_factory=list)
    summary: str = ""


class ContradictionItem(BaseModel):
    contradiction_type: str
    severity: str
    source: str
    timestamp: str
    impacted_state_fields: List[str] = Field(default_factory=list)
    reweave_required: bool = False
    notes: str = ""


class CoherenceReport(BaseModel):
    run_id: str
    mission_mode: str
    coherence_ok: bool = False

    supports_present_state: bool = False
    unresolved_contradictions: List[ContradictionItem] = Field(default_factory=list)
    goal_constraint_conflicts: List[str] = Field(default_factory=list)
    invalidated_assumptions: List[str] = Field(default_factory=list)

    confidence_score: float = 0.0
    instability_score: float = 1.0
    recommended_action_band: str = "read-only"


class OperatingFrame(BaseModel):
    run_id: str
    mission_mode: str
    current_objective: str

    active_goals: List[str] = Field(default_factory=list)
    hard_constraints: List[str] = Field(default_factory=list)

    allowed_actions: List[str] = Field(default_factory=list)
    blocked_actions: List[str] = Field(default_factory=list)

    top_risks: List[str] = Field(default_factory=list)
    top_open_loops: List[str] = Field(default_factory=list)
    relevant_ancestry: List[str] = Field(default_factory=list)
    contradiction_flags: List[str] = Field(default_factory=list)

    execution_confidence: float = 0.0
    instability_score: float = 1.0
    next_best_actions: List[str] = Field(default_factory=list)
