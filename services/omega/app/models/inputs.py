from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OmegaStrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=False,
        populate_by_name=True,
    )


class BoundedEnvironmentManifest(OmegaStrictModel):
    boundary: str = "bounded"
    horizon: int = Field(default=3, ge=1, le=64)
    observables: list[str] = Field(default_factory=list)
    error_budget: float = Field(default=0.25, ge=0.0, le=1.0)
    branch_cap: int = Field(default=4, ge=1, le=32)
    validation_cadence: str = "per_step"


class OmegaStateInput(OmegaStrictModel):
    state_id: str = Field(default_factory=lambda: f"omega_state_{uuid4().hex[:12]}")
    domain_type: str
    observed_at: datetime = Field(default_factory=utc_now)
    bounded_context: dict[str, Any] = Field(default_factory=dict)
    variables: dict[str, Any] = Field(default_factory=dict)
    constraints: dict[str, Any] = Field(default_factory=dict)
    observables: dict[str, Any] = Field(default_factory=dict)
    source_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    canon_version: int | None = None
    simulation_horizon: int = Field(default=3, ge=1, le=64)
    branch_count: int = Field(default=3, ge=1, le=32)
    metadata: dict[str, Any] = Field(default_factory=dict)
    environment_manifest: BoundedEnvironmentManifest = Field(
        default_factory=BoundedEnvironmentManifest
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_founder_payload(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        normalized = dict(data)
        bounded_context = normalized.get("bounded_context")
        if isinstance(bounded_context, str):
            normalized["bounded_context"] = {"description": bounded_context}

        if "state_id" not in normalized or not normalized.get("state_id"):
            normalized["state_id"] = f"omega_state_{uuid4().hex[:12]}"

        observables = normalized.get("observables")
        variables = normalized.get("variables", {})
        if isinstance(observables, list):
            normalized["observables"] = {
                str(name): variables.get(name) for name in observables if isinstance(name, str)
            }

        return normalized
