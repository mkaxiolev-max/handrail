from __future__ import annotations

from runtime.state.schemas import AncestryEdge, AncestryGraph, AncestryNode, PresentStateKernel


def retrieve_minimal_ancestry(run_id: str, present_state: PresentStateKernel) -> AncestryGraph:
    nodes = [
        AncestryNode(
            node_id="n1",
            node_type="user_directive",
            summary="Founder priority is to reduce human mediation between LLM planning and terminal execution.",
            source_ref="memory:user_directive",
        ),
        AncestryNode(
            node_id="n2",
            node_type="architecture_constraint",
            summary="Handrail is the execution bridge and should remain up during Boot EZ while NS and Continuum restart.",
            source_ref="runtime:handrail_boot_rule",
        ),
        AncestryNode(
            node_id="n3",
            node_type="execution",
            summary="Deterministic boot scripts and Handrail boot/run endpoints are already working.",
            source_ref="git:boot-baseline-v2+handrail-run-v1",
        ),
        AncestryNode(
            node_id="n4",
            node_type="commitment",
            summary="Present-state-first boot spine must produce explicit boot artifacts before broader autonomy.",
            source_ref="architecture:present_state_first",
        ),
    ]

    edges = [
        AncestryEdge(from_node="n1", to_node="n4", edge_type="explains"),
        AncestryEdge(from_node="n2", to_node="n3", edge_type="constrains"),
        AncestryEdge(from_node="n3", to_node="n4", edge_type="amplified_into"),
    ]

    return AncestryGraph(
        run_id=run_id,
        nodes=nodes,
        edges=edges,
        summary=(
            "Current state is primarily shaped by the founder directive to remove manual bridging, "
            "the Handrail uptime constraint during boot, and the recent successful deterministic boot baseline."
        ),
    )
