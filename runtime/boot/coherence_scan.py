from __future__ import annotations

from runtime.state.schemas import AncestryGraph, CoherenceReport, ContradictionItem, PresentStateKernel


def run_coherence_scan(run_id: str, present_state: PresentStateKernel, ancestry: AncestryGraph) -> CoherenceReport:
    contradictions = []
    conflicts = []
    invalidated = []

    if present_state.environment_status.get("boot_ok") is not True:
        contradictions.append(
            ContradictionItem(
                contradiction_type="runtime_health",
                severity="high",
                source="infra_boot",
                timestamp=present_state.boot_timestamp,
                impacted_state_fields=["engine_health", "environment_status"],
                reweave_required=True,
                notes="Runtime health did not fully support the claimed boot state.",
            )
        )

    if "bounded write with verification" not in present_state.allowed_action_bands:
        invalidated.append("bounded write actions are not currently permitted")

    coherence_ok = len(contradictions) == 0 and len(conflicts) == 0

    recommended_action_band = "bounded-write"
    if present_state.instability_score >= 0.5:
        recommended_action_band = "read-only"
    elif present_state.instability_score >= 0.3:
        recommended_action_band = "inspect-only"

    return CoherenceReport(
        run_id=run_id,
        mission_mode=present_state.mission_mode,
        coherence_ok=coherence_ok,
        supports_present_state=len(ancestry.nodes) > 0,
        unresolved_contradictions=contradictions,
        goal_constraint_conflicts=conflicts,
        invalidated_assumptions=invalidated,
        confidence_score=present_state.confidence_score,
        instability_score=present_state.instability_score,
        recommended_action_band=recommended_action_band,
    )
