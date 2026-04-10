"""Omega branch generation primitives."""

from __future__ import annotations

import random
from typing import Any


def _constraint_pressure(value: float, minimum: float | None, maximum: float | None) -> float:
    if minimum is not None and value < minimum:
        return min(1.0, (minimum - value) / (abs(minimum) + 1.0))
    if maximum is not None and value > maximum:
        return min(1.0, (value - maximum) / (abs(maximum) + 1.0))
    if minimum is not None and maximum is not None:
        span = max(maximum - minimum, 1.0)
        midpoint = minimum + span / 2
        distance = abs(value - midpoint) / (span / 2)
        return min(1.0, max(0.0, distance - 0.5))
    return 0.0


def generate_branches(normalized_state: dict[str, Any]) -> list[dict[str, Any]]:
    branch_total = normalized_state["branch_count"]
    variables = normalized_state["variables"]
    constraints = normalized_state["constraints"]
    rng = random.Random(normalized_state["seed"])

    branches: list[dict[str, Any]] = []
    variable_names = sorted(variables.keys())
    for branch_index in range(branch_total):
        branch_rng = random.Random(rng.randint(0, 10**9))
        perturbations: dict[str, float] = {}
        assumptions: list[str] = []

        for position, name in enumerate(variable_names):
            base_value = variables[name]
            amplitude = max(abs(base_value) * 0.08, 0.25)
            direction = -1.0 if (branch_index + position) % 2 else 1.0
            jitter = branch_rng.uniform(0.2, 1.0)
            perturbation = round(direction * amplitude * jitter, 4)
            perturbations[name] = perturbation
            assumptions.append(
                f"{name} initial perturbation {perturbation:+.4f} from observed baseline {base_value:.4f}"
            )

        constraint_pressure = 0.0
        for name, value in variables.items():
            spec = constraints.get(name, {})
            if isinstance(spec, dict):
                constraint_pressure += _constraint_pressure(
                    value + perturbations.get(name, 0.0),
                    spec.get("min"),
                    spec.get("max"),
                )

        branches.append(
            {
                "branch_index": branch_index,
                "assumptions": assumptions,
                "initial_variables": {
                    name: round(value + perturbations.get(name, 0.0), 4)
                    for name, value in variables.items()
                },
                "perturbations": perturbations,
                "constraint_pressure": round(
                    constraint_pressure / max(len(variable_names), 1),
                    4,
                ),
                "error_budget": normalized_state["environment_manifest"]["error_budget"],
            }
        )

    return branches
