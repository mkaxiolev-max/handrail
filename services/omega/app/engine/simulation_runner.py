"""Omega simulation runner."""

from __future__ import annotations

import uuid

from app.engine.branch_generator import generate_branches
from app.engine.confidence import score_confidence
from app.engine.divergence import score_divergence
from app.engine.state_model import normalize_state_input
from app.models.inputs import OmegaStateInput


def _build_transition_step(step_index: int, current_state: dict[str, float], branch: dict, normalized: dict) -> dict:
    drift_bias = float(normalized["metadata"].get("drift_bias", 0.05))
    error_budget = branch["error_budget"]
    constraints = normalized["constraints"]
    next_state: dict[str, float] = {}
    delta: dict[str, float] = {}
    notes: list[str] = []
    pressure_components: list[float] = []

    for variable_name, current_value in current_state.items():
        perturbation = branch["perturbations"].get(variable_name, 0.0)
        deterministic_bias = ((branch["branch_index"] + 1) * (step_index + 1) * drift_bias) / 10.0
        proposed_delta = perturbation * 0.35 + deterministic_bias
        proposed_value = round(current_value + proposed_delta, 4)
        next_state[variable_name] = proposed_value
        delta[variable_name] = round(proposed_delta, 4)

        spec = constraints.get(variable_name, {})
        if isinstance(spec, dict):
            minimum = spec.get("min")
            maximum = spec.get("max")
            if minimum is not None and proposed_value < minimum:
                notes.append(f"{variable_name} under minimum bound at step {step_index}")
                pressure_components.append(min(1.0, (minimum - proposed_value) / (abs(minimum) + 1.0)))
            elif maximum is not None and proposed_value > maximum:
                notes.append(f"{variable_name} over maximum bound at step {step_index}")
                pressure_components.append(min(1.0, (proposed_value - maximum) / (abs(maximum) + 1.0)))
            else:
                pressure_components.append(min(1.0, abs(proposed_delta) * error_budget))
        else:
            pressure_components.append(min(1.0, abs(proposed_delta) * error_budget))

    observed_state = {
        key: value for key, value in next_state.items() if key in normalized["observed_variables"]
    }
    inferred_state = {
        key: value for key, value in next_state.items() if key not in observed_state
    }

    return {
        "step_index": step_index,
        "observed_state": observed_state,
        "inferred_state": inferred_state,
        "delta": delta,
        "constraint_pressure": round(sum(pressure_components) / max(len(pressure_components), 1), 4),
        "notes": notes,
        "next_state": next_state,
    }


def _build_breach_points(transitions: list[dict], normalized: dict) -> list[dict]:
    breach_points: list[dict] = []
    for transition in transitions:
        for note in transition["notes"]:
            variable_name = note.split(" ", 1)[0]
            breach_points.append(
                {
                    "step_index": transition["step_index"],
                    "variable": variable_name,
                    "trigger": "constraint_breach",
                    "severity": transition["constraint_pressure"],
                    "description": note,
                }
            )

    if not breach_points and transitions:
        highest_pressure = max(transitions, key=lambda item: item["constraint_pressure"])
        if highest_pressure["constraint_pressure"] >= 0.35:
            dominant_variable = max(
                highest_pressure["delta"],
                key=lambda name: abs(highest_pressure["delta"][name]),
            )
            breach_points.append(
                {
                    "step_index": highest_pressure["step_index"],
                    "variable": dominant_variable,
                    "trigger": "material_separation",
                    "severity": highest_pressure["constraint_pressure"],
                    "description": f"{dominant_variable} is the dominant branch-separation driver.",
                }
            )
    return breach_points


def _intervention_candidates(branch_results: list[dict]) -> list[dict]:
    candidates: list[dict] = []
    for branch in branch_results:
        for breach in branch["breach_points"]:
            candidates.append(
                {
                    "step_index": breach["step_index"],
                    "variable": breach["variable"],
                    "action": f"Constrain {breach['variable']} before step {breach['step_index'] + 1}",
                    "expected_effect": "Reduce branch spread and lower breach severity.",
                    "leverage_score": round(min(1.0, breach["severity"] + 0.2), 4),
                }
            )
    candidates.sort(key=lambda item: item["leverage_score"], reverse=True)
    deduped: list[dict] = []
    seen: set[tuple[int, str]] = set()
    for candidate in candidates:
        key = (candidate["step_index"], candidate["variable"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped[:5]


async def run_simulation(state_input: OmegaStateInput) -> dict:
    normalized = normalize_state_input(state_input)
    run_id = f"omega_{uuid.uuid4().hex[:12]}"
    generated_branches = generate_branches(normalized)

    branch_results: list[dict] = []
    for branch in generated_branches:
        current_state = dict(branch["initial_variables"])
        transitions: list[dict] = []
        for step_index in range(normalized["simulation_horizon"]):
            transition = _build_transition_step(step_index, current_state, branch, normalized)
            current_state = transition.pop("next_state")
            transitions.append(transition)

        final_pressure = transitions[-1]["constraint_pressure"] if transitions else branch["constraint_pressure"]
        model_mismatch = round(
            min(1.0, abs(sum(branch["perturbations"].values())) / (len(branch["perturbations"]) + 1.0)),
            4,
        )
        breach_points = _build_breach_points(transitions, normalized)
        branch_results.append(
            {
                "branch_id": f"{run_id}_b{branch['branch_index']}",
                "parent_run_id": run_id,
                "branch_index": branch["branch_index"],
                "assumptions": branch["assumptions"],
                "transitions": transitions,
                "outputs": {
                    "final_state": current_state,
                    "observed_projection": {
                        key: value for key, value in current_state.items() if key in normalized["observed_variables"]
                    },
                    "inferred_projection": {
                        key: value for key, value in current_state.items() if key not in normalized["observed_variables"]
                    },
                    "disqualifiers": [item["description"] for item in breach_points],
                },
                "likelihood": 0.0,
                "confidence": {},
                "breach_points": breach_points,
                "divergence_components": {
                    "initial_perturbation": round(
                        abs(sum(branch["perturbations"].values())) / max(len(branch["perturbations"]), 1),
                        4,
                    ),
                    "constraint_pressure": round((branch["constraint_pressure"] + final_pressure) / 2.0, 4),
                    "model_mismatch": model_mismatch,
                },
                "provisional": True,
            }
        )

    divergence = score_divergence(branch_results)
    confidence_geometry = score_confidence(normalized, branch_results, divergence)

    for branch in branch_results:
        branch_stability = max(0.0, 1.0 - branch["divergence_components"]["initial_perturbation"])
        branch_overall_confidence = max(
            0.0,
            min(
                1.0,
                confidence_geometry["overall_confidence"] * 0.7
                + branch_stability * 0.15
                + (1.0 - branch["divergence_components"]["constraint_pressure"]) * 0.15,
            ),
        )
        branch["confidence"] = {
            **confidence_geometry,
            "branch_stability": round(branch_stability, 4),
            "overall_confidence": round(branch_overall_confidence, 4),
        }

    total_likelihood_denominator = sum(
        max(0.01, branch["confidence"]["overall_confidence"] * (1.0 - divergence["divergence_score"] / 2.0))
        for branch in branch_results
    )
    for branch in branch_results:
        raw_score = max(
            0.01,
            branch["confidence"]["overall_confidence"] * (1.0 - branch["divergence_components"]["constraint_pressure"]),
        )
        branch["likelihood"] = round(raw_score / total_likelihood_denominator, 4)

    ordered_branches = sorted(branch_results, key=lambda item: item["likelihood"], reverse=True)
    warnings = []
    if confidence_geometry["degraded"]:
        warnings.append("Low trust boundary: observability or stability is below target.")
    if divergence["divergence_score"] >= 0.6:
        warnings.append("High branch divergence: scenarios separate materially across the chosen horizon.")
    if any(branch["breach_points"] for branch in branch_results):
        warnings.append("At least one branch encounters a breach or disqualifier.")

    summary = {
        "most_likely_branch": ordered_branches[0]["branch_id"] if ordered_branches else None,
        "branch_spread": divergence["branch_spread"],
        "divergence_score": divergence["divergence_score"],
        "confidence_geometry": confidence_geometry,
        "key_branch_points": [item for branch in ordered_branches for item in branch["breach_points"]][:5],
        "intervention_candidates": _intervention_candidates(ordered_branches),
        "warnings": warnings,
        "epistemic_boundary": confidence_geometry["epistemic_boundary"],
    }

    return {
        "run_id": run_id,
        "normalized_input": normalized,
        "branches": ordered_branches,
        "summary": summary,
        "confidence": confidence_geometry,
        "divergence": divergence,
        "warnings": warnings,
    }
