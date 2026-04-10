"""Omega divergence scoring primitives."""

from __future__ import annotations

from itertools import combinations


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def score_divergence(branch_results: list[dict]) -> dict:
    if len(branch_results) <= 1:
        return {
            "divergence_score": 0.0,
            "spread": 0.0,
            "sensitivity": 0.0,
            "constraint_pressure": 0.0,
            "model_mismatch": 0.0,
            "branch_spread": {},
        }

    final_states = [branch["outputs"]["final_state"] for branch in branch_results]
    variable_names = sorted({key for state in final_states for key in state.keys()})

    branch_spread: dict[str, float] = {}
    for name in variable_names:
        values = [float(state.get(name, 0.0)) for state in final_states]
        branch_spread[name] = round(max(values) - min(values), 4)

    pairwise_distances: list[float] = []
    for left, right in combinations(final_states, 2):
        distance = 0.0
        for name in variable_names:
            distance += abs(float(left.get(name, 0.0)) - float(right.get(name, 0.0)))
        pairwise_distances.append(distance / max(len(variable_names), 1))

    spread = _mean(list(branch_spread.values()))
    sensitivity = _mean(pairwise_distances)
    constraint_pressure = _mean(
        [branch["divergence_components"].get("constraint_pressure", 0.0) for branch in branch_results]
    )
    model_mismatch = _mean(
        [branch["divergence_components"].get("model_mismatch", 0.0) for branch in branch_results]
    )

    divergence_score = min(
        1.0,
        (spread * 0.35) + (sensitivity * 0.3) + (constraint_pressure * 0.2) + (model_mismatch * 0.15),
    )

    return {
        "divergence_score": round(divergence_score, 4),
        "spread": round(spread, 4),
        "sensitivity": round(sensitivity, 4),
        "constraint_pressure": round(constraint_pressure, 4),
        "model_mismatch": round(model_mismatch, 4),
        "branch_spread": branch_spread,
    }
