"""Basic integrity types used across rings."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


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
