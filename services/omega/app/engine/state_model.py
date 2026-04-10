"""Omega state normalization helpers."""

from __future__ import annotations

import hashlib
from typing import Any

from app.models.inputs import OmegaStateInput


def _stable_seed(state_id: str, metadata: dict[str, Any]) -> int:
    if "seed" in metadata:
        return int(metadata["seed"])
    digest = hashlib.sha256(state_id.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _normalize_numeric_map(values: dict[str, Any]) -> dict[str, float]:
    normalized: dict[str, float] = {}
    for key, value in values.items():
        if isinstance(value, bool):
            normalized[key] = 1.0 if value else 0.0
        elif isinstance(value, (int, float)):
            normalized[key] = float(value)
    return normalized


def normalize_state_input(state_input: OmegaStateInput) -> dict[str, Any]:
    raw_variables = dict(state_input.variables)
    variables = _normalize_numeric_map(raw_variables)
    categorical_variables = {
        key: value for key, value in raw_variables.items() if key not in variables
    }
    observables = dict(state_input.observables)
    observed_variables = {
        key: value for key, value in variables.items() if key in observables or key in state_input.environment_manifest.observables
    }
    inferred_variables = {
        key: value for key, value in variables.items() if key not in observed_variables
    }
    constraints = dict(state_input.constraints)
    manifest = state_input.environment_manifest.model_dump(mode="json")
    manifest["horizon"] = state_input.simulation_horizon
    manifest["branch_cap"] = min(manifest["branch_cap"], state_input.branch_count)

    return {
        "state_id": state_input.state_id,
        "domain_type": state_input.domain_type,
        "observed_at": state_input.observed_at,
        "bounded_context": dict(state_input.bounded_context),
        "variables": variables,
        "categorical_variables": categorical_variables,
        "observed_variables": observed_variables,
        "inferred_variables": inferred_variables,
        "constraints": constraints,
        "observables": observables,
        "source_refs": list(state_input.source_refs),
        "receipt_refs": list(state_input.receipt_refs),
        "canon_version": state_input.canon_version,
        "simulation_horizon": state_input.simulation_horizon,
        "branch_count": state_input.branch_count,
        "metadata": dict(state_input.metadata),
        "environment_manifest": manifest,
        "seed": _stable_seed(state_input.state_id, state_input.metadata),
    }
