from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
from uuid import uuid4

HyperObjectID = str

def new_hoid() -> HyperObjectID:
    return f"urn:uuid:{uuid4()}"

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

class VerificationStatus(str, Enum):
    unverified = "unverified"
    supported = "supported"
    contradicted = "contradicted"
    unknown = "unknown"

class Claim(BaseModel):
    claim_id: HyperObjectID = Field(default_factory=new_hoid)
    text: str
    verification_status: VerificationStatus = VerificationStatus.unverified
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    evidence_refs: list[HyperObjectID] = Field(default_factory=list)

class EpistemicAxis(BaseModel):
    claims: list[Claim] = Field(default_factory=list)
    overall_confidence: float = Field(ge=0.0, le=1.0, default=0.5)

class ExecutionStatus(str, Enum):
    proposed = "proposed"
    authorized = "authorized"
    running = "running"
    completed = "completed"
    failed = "failed"
    rolled_back = "rolled_back"

class ExecutionStep(BaseModel):
    step_id: str
    action: str
    status: ExecutionStatus = ExecutionStatus.proposed
    receipt_ref: HyperObjectID | None = None

class ExecutionAxis(BaseModel):
    intent: str = ""
    status: ExecutionStatus = ExecutionStatus.proposed
    steps: list[ExecutionStep] = Field(default_factory=list)
    side_effects: list[str] = Field(default_factory=list)

class PolicyDecision(str, Enum):
    allow = "allow"
    deny = "deny"
    allow_with_obligations = "allow_with_obligations"

class PolicyAxis(BaseModel):
    decision: PolicyDecision = PolicyDecision.allow
    ruleset_id: str = "policy://ns/default/v1"
    obligations: list[dict] = Field(default_factory=list)
    denials: list[dict] = Field(default_factory=list)
    evaluation_hash: str = ""

class MemoryAxis(BaseModel):
    stores: list[str] = Field(default_factory=lambda: ["alexandria:durable"])
    retention_locked: bool = False
    index_refs: list[str] = Field(default_factory=list)
    promotion_state: str = "working"

class ExposureAxis(BaseModel):
    allowed_audiences: list[str] = Field(default_factory=lambda: ["ns:internal"])
    redaction_profile: str = "redaction://profile/default"
    provider_constraints: list[dict] = Field(default_factory=list)

class TemporalAxis(BaseModel):
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)
    valid_from: str | None = None
    valid_to: str | None = None
    ttl_seconds: int | None = None

class IdentityAxis(BaseModel):
    owner_id: str = "founder"
    actor_bindings: list[str] = Field(default_factory=list)
    continuity_keys: list[str] = Field(default_factory=list)

class NarrativeAxis(BaseModel):
    summary: str = ""
    rationale: str = ""
    user_visible_receipts: list[HyperObjectID] = Field(default_factory=list)
    derivation_verified: bool = False

class SensitivityClassification(str, Enum):
    public = "public"
    internal = "internal"
    confidential = "confidential"
    restricted = "restricted"

class SensitivityAxis(BaseModel):
    classification: SensitivityClassification = SensitivityClassification.internal
    pii_tags: list[str] = Field(default_factory=list)
    allow_external_providers: bool = False

class HyperObject(BaseModel):
    id: HyperObjectID = Field(default_factory=new_hoid)
    version: int = 1
    receipt_refs: list[HyperObjectID] = Field(default_factory=list)
    temporal: TemporalAxis = Field(default_factory=TemporalAxis)
    sensitivity: SensitivityAxis = Field(default_factory=SensitivityAxis)
    exposure: ExposureAxis = Field(default_factory=ExposureAxis)
    epistemic: EpistemicAxis = Field(default_factory=EpistemicAxis)
    execution: ExecutionAxis = Field(default_factory=ExecutionAxis)
    policy: PolicyAxis = Field(default_factory=PolicyAxis)
    memory: MemoryAxis = Field(default_factory=MemoryAxis)
    identity: IdentityAxis = Field(default_factory=IdentityAxis)
    narrative: NarrativeAxis = Field(default_factory=NarrativeAxis)

    def content_hash(self) -> str:
        return hashlib.sha256(
            json.dumps(self.model_dump(), sort_keys=True, default=str).encode()
        ).hexdigest()

    def bump_version(self) -> "HyperObject":
        updated = self.model_copy(deep=True)
        updated.version += 1
        updated.temporal.updated_at = utc_now()
        return updated

class TransformType(str, Enum):
    propose_plan = "PROPOSE_PLAN"
    authorize_action = "AUTHORIZE_ACTION"
    execute_action = "EXECUTE_ACTION"
    ingest_memory = "INGEST_MEMORY"
    promote_memory = "PROMOTE_MEMORY"
    publish_narrative = "PUBLISH_NARRATIVE"
    update_sensitivity = "UPDATE_SENSITIVITY"
    update_epistemic = "UPDATE_EPISTEMIC"
    update_policy = "UPDATE_POLICY"

class TransformRequest(BaseModel):
    transform_id: HyperObjectID = Field(default_factory=new_hoid)
    type: TransformType
    actor: str
    target_object_id: HyperObjectID
    input_projection_name: str
    patch: dict[str, Any] = Field(default_factory=dict)
    trace_context: dict[str, str] = Field(default_factory=dict)

    ALLOWED_AXES: dict = {
        "PROPOSE_PLAN": ["execution", "epistemic"],
        "AUTHORIZE_ACTION": ["execution", "policy"],
        "EXECUTE_ACTION": ["execution", "policy", "memory"],
        "INGEST_MEMORY": ["memory", "sensitivity"],
        "PROMOTE_MEMORY": ["memory"],
        "PUBLISH_NARRATIVE": ["narrative", "epistemic"],
        "UPDATE_SENSITIVITY": ["sensitivity", "exposure"],
        "UPDATE_EPISTEMIC": ["epistemic"],
        "UPDATE_POLICY": ["policy"],
    }

    def axes_allowed(self) -> list[str]:
        return self.ALLOWED_AXES.get(self.type.value, [])
