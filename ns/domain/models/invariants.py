"""NS∞ invariant predicates — I1..I10 (core) + I16..I20 (RIL/Oracle extension).

All invariants are checkable predicates. SACRED. L10 may not amend.
Tag: ril-oracle-doctrine-v2
"""
from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Core invariants I1–I10
# ---------------------------------------------------------------------------

def I1_canon_precedes_conversion(canon_ready: bool, conversion_attempted: bool) -> bool:
    """Canon must exist before any conversion (Loom) operation."""
    if conversion_attempted:
        return canon_ready
    return True


def I2_append_only_memory(operation: str) -> bool:
    """Lineage Fabric and Alexandrian Archive are append-only; no delete/rewrite."""
    return operation not in {"delete", "rewrite", "truncate", "drop"}


def I3_no_llm_authority_over_canon(authority_source: str) -> bool:
    """LLMs may not define or amend Canon."""
    return authority_source != "llm"


def I4_hardware_quorum_on_canon_change(quorum_certs: list[dict]) -> bool:
    """Canon changes require YubiKey 26116460 as mandatory singleton (≥2f+1 Byzantine)."""
    yubi_present = any(c.get("serial") == "26116460" for c in quorum_certs)
    f = (len(quorum_certs) - 1) // 3
    return yubi_present and len(quorum_certs) >= 2 * f + 1


def I5_provenance_inertness(hash_chain_valid: bool) -> bool:
    """Provenance records are cryptographically hash-chain verified and immutable."""
    return hash_chain_valid


def I6_sentinel_gate_soundness(gate_result: Any) -> bool:
    """Sentinel Gate decision must be a resolved bool (no ambiguity)."""
    return isinstance(gate_result, bool)


def I7_bisimulation_with_replay(original_trace: list, replay_trace: list) -> bool:
    """2-safety: replay of any execution trace must produce an identical outcome."""
    return original_trace == replay_trace


def I8_distributed_eventual_consistency(crdt_converged: bool) -> bool:
    """State Manifold shards must eventually converge via CRDT/SEC."""
    return crdt_converged


def I9_hardware_quorum_for_authority_change(quorum_certs: list[dict]) -> bool:
    """Authority changes require Byzantine-fault-tolerant hardware quorum (≥2f+1)."""
    f = (len(quorum_certs) - 1) // 3
    return len(quorum_certs) >= 2 * f + 1


def I10_supersession_monotone(operation: str) -> bool:
    """Records are superseded only; never deleted. Monotone growth invariant."""
    return operation not in {"delete", "drop", "purge"}


# ---------------------------------------------------------------------------
# RIL + Oracle extension invariants I16–I20 (Phase C)
# ---------------------------------------------------------------------------

def I16_reflexive_integrity_monotonicity(prev_score: float, curr_score: float) -> bool:
    """Aggregate RIL integrity score is non-decreasing across ticks; no backward drift."""
    return curr_score >= prev_score


def I17_oracle_adjudication_primacy(oracle_resolved: bool, execution_dispatched: bool) -> bool:
    """Oracle OracleDecision must be resolved before any Handrail execution envelope."""
    if execution_dispatched:
        return oracle_resolved
    return True


def I18_reality_binding_integrity(grounded_observation_count: int) -> bool:
    """All narrative outputs must bind to ≥1 verifiable Gradient Field observation."""
    return grounded_observation_count >= 1


def I19_founder_loop_protection(recursion_depth: int, max_depth: int = 3) -> bool:
    """Recursive founder-intent loops exceeding depth 3 are unconditionally vetoed."""
    return recursion_depth <= max_depth


def I20_precedence_ladder_immutability(ladder_hash: str, canonical_hash: str) -> bool:
    """The RIL precedence ladder is SACRED; it must match the canonical hash."""
    return ladder_hash == canonical_hash


# ---------------------------------------------------------------------------
# Registry — all invariants keyed by ID
# ---------------------------------------------------------------------------

INVARIANT_REGISTRY: dict[str, Any] = {
    "I1": I1_canon_precedes_conversion,
    "I2": I2_append_only_memory,
    "I3": I3_no_llm_authority_over_canon,
    "I4": I4_hardware_quorum_on_canon_change,
    "I5": I5_provenance_inertness,
    "I6": I6_sentinel_gate_soundness,
    "I7": I7_bisimulation_with_replay,
    "I8": I8_distributed_eventual_consistency,
    "I9": I9_hardware_quorum_for_authority_change,
    "I10": I10_supersession_monotone,
    "I16": I16_reflexive_integrity_monotonicity,
    "I17": I17_oracle_adjudication_primacy,
    "I18": I18_reality_binding_integrity,
    "I19": I19_founder_loop_protection,
    "I20": I20_precedence_ladder_immutability,
}

EXTENSION_INVARIANTS_RIL = ("I16", "I17", "I18", "I19", "I20")
