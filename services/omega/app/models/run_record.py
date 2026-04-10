from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from app.models.inputs import OmegaStrictModel, utc_now


class OmegaRunRecord(OmegaStrictModel):
    run_id: str
    created_at: datetime = Field(default_factory=utc_now)
    actor: str
    domain_type: str
    input_ref: str
    branch_count: int = Field(ge=1, le=32)
    horizon: int = Field(ge=1, le=64)
    status: str
    receipt_hash: str
    chain_verified: bool
    memory_refs: list[str] = Field(default_factory=list)
    simulation_class: str = "bounded_causal_simulation"
    provisional: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    def with_memory_refs(self, memory_refs: list[str]) -> "OmegaRunRecord":
        self.memory_refs = memory_refs
        return self
