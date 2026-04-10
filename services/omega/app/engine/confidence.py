"""Omega confidence scoring primitives."""

from __future__ import annotations


def score_confidence(
    normalized_state: dict,
    branch_results: list[dict],
    divergence: dict,
) -> dict:
    variable_count = max(len(normalized_state["variables"]), 1)
    observed_count = len(normalized_state["observed_variables"])
    evidence_depth = min(
        1.0,
        (len(normalized_state["source_refs"]) + len(normalized_state["receipt_refs"])) / max(variable_count, 2),
    )
    observability = min(1.0, observed_count / variable_count)
    branch_stability = max(0.0, 1.0 - divergence["sensitivity"])
    divergence_pressure = min(1.0, divergence["divergence_score"])
    avg_model_mismatch = sum(
        branch["divergence_components"].get("model_mismatch", 0.0) for branch in branch_results
    ) / max(len(branch_results), 1)
    model_fit = max(0.0, 1.0 - avg_model_mismatch)
    avg_constraint_pressure = sum(
        branch["divergence_components"].get("constraint_pressure", 0.0) for branch in branch_results
    ) / max(len(branch_results), 1)
    constraint_satisfaction = max(0.0, 1.0 - avg_constraint_pressure)
    overall_confidence = max(
        0.0,
        min(
            1.0,
            (
                evidence_depth * 0.18
                + observability * 0.22
                + branch_stability * 0.18
                + model_fit * 0.18
                + constraint_satisfaction * 0.14
                + (1.0 - divergence_pressure) * 0.10
            ),
        ),
    )
    degraded = overall_confidence < 0.55 or observability < 0.4

    if degraded:
        epistemic_boundary = (
            "Low observability or unstable branching limits trust; treat results as exploratory only."
        )
    else:
        epistemic_boundary = (
            "Bounded simulation is coherent within declared constraints, but remains provisional."
        )

    return {
        "evidence_depth": round(evidence_depth, 4),
        "observability": round(observability, 4),
        "branch_stability": round(branch_stability, 4),
        "divergence_pressure": round(divergence_pressure, 4),
        "model_fit": round(model_fit, 4),
        "constraint_satisfaction": round(constraint_satisfaction, 4),
        "overall_confidence": round(overall_confidence, 4),
        "degraded": degraded,
        "epistemic_boundary": epistemic_boundary,
    }
