"""Authoritative receipt names for the Lineage Fabric."""
from __future__ import annotations

RECEIPT_NAMES: frozenset[str] = frozenset(
    {
        # RIL receipts (T3 owns bodies)
        "ril_evaluation_started",
        "ril_drift_checked",
        "ril_grounding_checked",
        "ril_encounter_interrupt_triggered",
        "ril_reality_binding_checked",
        "ril_route_effects_emitted",
        # Oracle receipts (T3 owns bodies)
        "oracle_received_ril_packet",
        "oracle_adjudicated_with_integrity_state",
        "oracle_handrail_envelope_built",
        # Storytime / interface
        "storytime_humility_entered",
        "interface_recalibration_entered",
        "interface_recalibration_completed",
        "handrail_scope_narrowed_by_ril",
        # T1 Ring 2–6
        "ring6_g2_invariant_checked",
        "canon_promoted_with_hardware_quorum",
        "canon_promotion_denied_i9_quorum_missing",
        "lineage_fabric_appended",
        "alexandrian_lexicon_baptism_receipted",
        "alexandrian_lexicon_drift_blocked",
        "narrative_emitted_with_receipt_hash",
        # T1 Ring 3 — The Loom (L4)
        "loom_reflection_completed",
        "loom_mode_transitioned",
        "loom_contradiction_injected",
        # T4 (reserved)
        "dimensional_contradiction_detected",
        "manifold_projection_lawful",
    }
)
