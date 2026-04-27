"""PAP v1.0 schemas — Pydantic v1+v2 dual-compatible."""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
from enum import Enum


class EpistemicType(str, Enum):
    OBSERVED_FACT       = "observed_fact"
    REPORTED_CLAIM      = "reported_claim"
    DERIVED_INFERENCE   = "derived_inference"
    SPECULATION         = "speculation"
    LEGAL_STATUS_EVENT  = "legal_status_event"
    NARRATIVE_FRAME     = "narrative_frame"


StorytimeMode = Literal[
    "CANONICAL_EXPLANATION",
    "SPECULATIVE_REFLECTION",
    "IDENTITY_CONTINUITY",
    "SYMBOLIC_INTERPRETATION",
    "NARRATIVE_AS_PROOF",  # FORBIDDEN — rejected at validate
]

PAPMode = Literal["H", "A", "T", "ALL"]

PAPDecision = Literal[
    "ALLOW", "DENY", "WITHHOLD", "BRANCH",
    "HARD_STOP", "ADMIT", "REFUSE_COLLAPSE",
]


class HumanSurface(BaseModel):
    summary: str
    explanation: str
    ui_schema: Optional[Dict[str, Any]] = None
    persuasion_flags: List[str] = []
    storytime_mode: StorytimeMode = "CANONICAL_EXPLANATION"


class PAPAction(BaseModel):
    action_id: str
    endpoint: str
    method: Literal["GET", "POST", "PATCH", "DELETE"]
    constraints: Dict[str, Any] = {}
    reversibility_score: float = Field(ge=0.0, le=1.0, default=1.0)
    irreversible: bool = False
    handrail_required: bool = True
    required_receipts: List[str] = []
    logos_check_required: bool = True
    canon_check_required: bool = True


class AgentSurface(BaseModel):
    schema_ref: str
    affordances: List[PAPAction] = []


class PAPEvidence(BaseModel):
    evidence_id: str
    source_uri: str
    hash: str
    timestamp: datetime
    provenance: Dict[str, Any] = {}


class PAPClaim(BaseModel):
    claim_id: str
    text: str
    epistemic_type: EpistemicType
    evidence_refs: List[str] = []
    confidence: float = Field(ge=0.0, le=1.0)


class TruthSurface(BaseModel):
    claims: List[PAPClaim] = []
    evidence: List[PAPEvidence] = []
    inferences: List[Dict[str, Any]] = []
    contradictions: List[Dict[str, Any]] = []
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    canon_eligibility: Dict[str, Any] = {"eligible": False, "reason": "default"}


class PAPIdentity(BaseModel):
    actor_id: Optional[str] = None
    session_hash: str
    ctf_lineage_id: str


class AletheiaPAPResource(BaseModel):
    resource_id: str
    pap_version: Literal["1.0"] = "1.0"
    merkle_root: str
    identity: PAPIdentity
    H: HumanSurface
    A: AgentSurface
    T: TruthSurface
    receipts: Dict[str, Any] = {}
    deletion: Dict[str, Any] = {
        "active_surface_ttl": "P30D",
        "debris_policy": "retain_lineage_delete_surface",
        "supersedes": [],
    }
    scoring: Dict[str, Any] = {}


class PAPReceipt(BaseModel):
    receipt_type: Literal["pap"] = "pap"
    receipt_id: str
    timestamp: datetime
    resource_id: str
    decision: PAPDecision
    pap_score: float = Field(ge=0.0, le=100.0)
    aletheion_receipt_refs: List[str] = []
    handrail_receipt_ref: Optional[str] = None
    qec_syndromes_fired: List[str] = []
    reasons: List[str] = []
    hash: str


class PAPQECFailure(BaseModel):
    syndrome: Literal["S1","S2","S3","S4","S5","S6","S7","S8","S9","S10"]
    description: str
    field_path: Optional[str] = None
    severity: float = Field(ge=0.0, le=1.0, default=1.0)


class PAPScore(BaseModel):
    score_total: float = Field(ge=0.0, le=100.0)
    grade: Literal[
        "WEB_PAGE","STRUCTURED","AGENT_USABLE",
        "GOVERNED_PARITY","CANON_READY","THEORETICAL_MAX",
    ]
    subscores: Dict[str, float]


class TriadicScore(BaseModel):
    ldr_score: float = Field(ge=0.0, le=100.0)
    omega_gnoseo_score: float = Field(ge=0.0, le=100.0)
    pap_score: float = Field(ge=0.0, le=100.0)
    triadic_min: float = Field(ge=0.0, le=100.0)
    canon_eligible: bool
    blocking_track: Optional[Literal["LDR","OMEGA_GNOSEO","PAP"]] = None
