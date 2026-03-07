from __future__ import annotations

from runtime.state.schemas import AncestryGraph, CoherenceReport, OperatingFrame, PresentStateKernel


def build_operating_frame(
    run_id: str,
    present_state: PresentStateKernel,
    ancestry: AncestryGraph,
    coherence: CoherenceReport,
) -> OperatingFrame:
    blocked = []
    if coherence.recommended_action_band == "read-only":
        blocked = ["destructive-write", "unbounded-exec", "state-changing-ops"]
    elif coherence.recommended_action_band == "inspect-only":
        blocked = ["destructive-write", "unbounded-exec"]

    contradiction_flags = [
        f"{c.contradiction_type}:{c.severity}"
        for c in coherence.unresolved_contradictions
    ]

    return OperatingFrame(
        run_id=run_id,
        mission_mode=present_state.mission_mode,
        current_objective=present_state.current_objective,
        active_goals=present_state.active_goals,
        hard_constraints=present_state.hard_constraints,
        allowed_actions=present_state.allowed_action_bands,
        blocked_actions=blocked,
        top_risks=present_state.current_risks,
        top_open_loops=present_state.unresolved_commitments,
        relevant_ancestry=[n.summary for n in ancestry.nodes],
        contradiction_flags=contradiction_flags,
        execution_confidence=coherence.confidence_score,
        instability_score=coherence.instability_score,
        next_best_actions=[
            "write boot artifacts",
            "prepare one bounded Handrail packet",
            "execute one read-heavy Handrail task",
        ],
    )
