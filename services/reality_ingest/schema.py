"""RIS canonical schema with source-adaptive provenance."""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import hashlib, orjson


class EpistemicClass(str, Enum):
    OBSERVED_FACT       = "observed_fact"
    REPORTED_CLAIM      = "reported_claim"
    LEGAL_STATUS_EVENT  = "legal_status_event"


class SourceLane(str, Enum):
    PATENTSVIEW_S3      = "patentsview_s3"
    USPTO_ODP_API       = "uspto_odp_api"
    LOCAL_INBOX         = "local_inbox"
    LEGACY_BULKDATA     = "legacy_bulkdata"
    UNAVAILABLE         = "unavailable"


class SourceTier(str, Enum):
    OFFICIAL_AUTHENTICATED = "official_authenticated"
    OFFICIAL_PUBLIC        = "official_public"
    DERIVED_PUBLIC         = "derived_public"
    MANUAL                 = "manual"
    UNVERIFIED             = "unverified"


class FieldProvenance(BaseModel):
    field: str
    present: bool
    reason: Optional[str] = None


class RealityObject(BaseModel):
    id: str
    source: str
    type: str
    source_lane: SourceLane
    source_tier: SourceTier
    source_url: Optional[str] = None
    source_resolved_at: datetime
    source_receipt_id: str
    title: Optional[str] = None
    abstract: Optional[str] = None
    claims: List[str] = Field(default_factory=list)
    inventors: List[str] = Field(default_factory=list)
    assignees: List[str] = Field(default_factory=list)
    filing_date: Optional[datetime] = None
    publication_date: Optional[datetime] = None
    grant_date: Optional[datetime] = None
    cpc_codes: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    family_ids: List[str] = Field(default_factory=list)
    epistemic_class: EpistemicClass
    credibility: float = 0.0
    novelty: float = 0.0
    impact: float = 0.0
    technical_validity: float = 0.0
    narrative_momentum: float = 0.0
    raw_source_pointer: str
    ingestion_receipt_id: str
    field_provenance: List[FieldProvenance] = Field(default_factory=list)

    def canonical_bytes(self) -> bytes:
        return orjson.dumps(self.model_dump(mode="json"), option=orjson.OPT_SORT_KEYS)

    def content_hash(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


class SourceCandidate(BaseModel):
    lane: SourceLane
    tier: SourceTier
    url: Optional[str] = None
    file_pointer: Optional[str] = None
    available: bool
    reason: Optional[str] = None
    probe_status: Optional[int] = None
    probe_content_type: Optional[str] = None
    probe_byte_size: Optional[int] = None


class SourceResolutionResult(BaseModel):
    receipt_id: str
    timestamp: datetime
    target: str
    candidates_tried: List[SourceCandidate]
    chosen: Optional[SourceCandidate] = None
    chosen_lane: SourceLane
    chosen_tier: SourceTier
    success: bool
    drift_detected: bool = False
    drift_notes: List[str] = Field(default_factory=list)


class StageReceipt(BaseModel):
    receipt_id: str
    stage: str
    timestamp: datetime
    input_pointer: str
    output_pointer: str
    record_count: int = 0
    bytes_in: int = 0
    bytes_out: int = 0
    sha256_in: Optional[str] = None
    sha256_out: Optional[str] = None
    prev_receipt_sha: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    duration_ms: int = 0
    metadata: dict = Field(default_factory=dict)


class IngestionReceipt(BaseModel):
    receipt_id: str
    object_id: str
    source: str
    source_lane: SourceLane
    source_receipt_id: str
    epistemic_class: EpistemicClass
    raw_sha256: str
    normalized_sha256: str
    fetch_receipt_id: str
    parse_receipt_id: str
    normalize_receipt_id: str
    score_receipt_id: str
    persist_receipt_id: str
    timestamp: datetime
    pipeline_version: str = "2.0.0-source-adaptive"
