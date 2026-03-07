from __future__ import annotations

from runtime.state.schemas import InfraBootReport, PresentStateKernel


def synthesize_present_state(infra: InfraBootReport) -> PresentStateKernel:
    ns_health = infra.endpoint_status.get("ns", {})
    handrail_health = infra.endpoint_status.get("handrail", {})
    continuum_state = infra.endpoint_status.get("continuum", {})

    boot_ok = (
        infra.dependency_status.get("handrail_ok")
        and infra.dependency_status.get("ns_ok")
        and infra.dependency_status.get("continuum_ok")
    )

    active_goals = [
        "containers healthy",
        "present state kernel generated",
        "ancestry retrieved",
        "coherence report published",
        "operating frame published",
        "bounded Handrail execution packet prepared",
    ]

    hard_constraints = [
        "no unsafe terminal execution",
        "preserve raw audit trail",
        "do not silently discard contradictions",
    ]

    soft_constraints = [
        "minimize context size",
        "reduce founder intervention",
        "prefer deterministic checks over narrative assumptions",
    ]

    current_risks = []
    if not boot_ok:
        current_risks.append("runtime not fully healthy")
    if not infra.storage_status.get("external_ssd"):
        current_risks.append("external storage not confirmed")

    return PresentStateKernel(
        mission_mode="boot_integration",
        current_objective="establish present-state-first boot spine and prepare structured Handrail execution",
        active_goals=active_goals,
        hard_constraints=hard_constraints,
        soft_constraints=soft_constraints,
        unresolved_commitments=[
            "Handrail beta path",
            "next boot reliability",
            "direct LLM-to-terminal bridge",
        ],
        current_risks=current_risks or [
            "narrative self-sealing",
            "plan-execution drift",
            "overloading boot with history",
        ],
        engine_health={
            "handrail": "healthy" if handrail_health.get("ok") else "degraded",
            "ns": "healthy" if ns_health.get("status") == "ok" else "degraded",
            "continuum": "healthy" if "global_tier" in continuum_state else "degraded",
        },
        environment_status={
            "external_ssd": infra.storage_status.get("external_ssd", False),
            "ns_ssd_mounted": infra.storage_status.get("ns_ssd_mounted", False),
            "boot_ok": boot_ok,
        },
        active_domains=[
            "boot",
            "runtime",
            "execution",
        ],
        resonance_weights={
            "runtime_integrity": 1.0,
            "execution_bridge": 0.95,
            "memory_reconstruction": 0.7,
        },
        allowed_action_bands=[
            "read",
            "inspect",
            "diff",
            "health-check",
            "bounded write with verification",
        ] if boot_ok else [
            "read",
            "inspect",
            "health-check",
        ],
        operator_override_flags={
            "founder_veto_active": True,
        },
        confidence_score=0.85 if boot_ok else 0.45,
        instability_score=0.20 if boot_ok else 0.65,
        boot_timestamp=infra.boot_timestamp,
    )
