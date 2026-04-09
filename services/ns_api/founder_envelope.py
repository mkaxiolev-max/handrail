from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Any

class FounderResponseEnvelope(BaseModel):
    status: str
    receipt_hash: str
    chain_verified: bool
    mode: str
    pressure: str | None = None
    response_shape: str | None = None
    canon_version: int | None = None
    canon_hash: str | None = None
    memory_atoms_written: int = 0
    memory_atoms_queried: int = 0
    feed_items_added: int = 0
    voice_session_id: str | None = None
    result: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None

    class Config:
        extra = "forbid"
