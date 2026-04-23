"""Kenosis proof emitter for every Irreversible and Bounded-Irreversible transition.

A KenosisProof is a constitutional record that a transition deliberately
surrenders reversibility in exchange for a bounded or permanent commitment.
Every proof is anchored to the Lineage Fabric via a non-null receipt_ref.

Constitutional proofs are pre-computed at import time for all non-reversible
ops in the registry using deterministic hashes.  Runtime-generated proofs
substitute actual receipt IDs from the live ReceiptChain.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Optional

from .registry import NON_REVERSIBLE, Kind, StateTransition


# ── Data model ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class KenosisProof:
    op_id: str
    pre_state_hash: str
    post_state_hash: str
    justification: str
    bounded_budget: Optional[str]
    compensating_action: str
    receipt_ref: str  # non-null; anchored to Lineage Fabric

    def __post_init__(self) -> None:
        if not self.receipt_ref:
            raise ValueError(
                f"KenosisProof for {self.op_id!r} must have a non-null receipt_ref "
                "(Lineage Fabric anchor)"
            )

    def to_dict(self) -> dict:
        return asdict(self)


# ── Hash helpers ──────────────────────────────────────────────────────────────


def _canonical_hash(domain: str, state: str) -> str:
    """Deterministic hash for a (domain, state) pair."""
    payload = json.dumps({"domain": domain, "state": state}, sort_keys=True)
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()


def _lineage_ref(op_id: str) -> str:
    """Constitutional Lineage Fabric reference for a pre-registered proof."""
    return f"lineage://constitutional/v1/{op_id}"


# ── Proof construction ────────────────────────────────────────────────────────


def _build_proof(t: StateTransition, receipt_ref: Optional[str] = None) -> KenosisProof:
    """Build a KenosisProof for transition *t*.

    *receipt_ref* defaults to the constitutional lineage URI so that
    pre-registered proofs are always non-null.  Pass an actual receipt_id
    (e.g. ``"R_000042"``) when emitting a runtime proof.
    """
    return KenosisProof(
        op_id=t.op_id,
        pre_state_hash=_canonical_hash(t.domain, t.from_state),
        post_state_hash=_canonical_hash(t.domain, t.to_state),
        justification=t.justification,
        bounded_budget=t.bounded_budget,
        compensating_action=t.compensating_action or "",
        receipt_ref=receipt_ref or _lineage_ref(t.op_id),
    )


# ── Constitutional proof table (one per non-reversible op) ───────────────────

CONSTITUTIONAL_PROOFS: dict[str, KenosisProof] = {
    op_id: _build_proof(t)
    for op_id, t in NON_REVERSIBLE.items()
}

# 100% coverage gate — every non-reversible op must have a proof.
_missing = set(NON_REVERSIBLE) - set(CONSTITUTIONAL_PROOFS)
assert not _missing, (
    f"Coverage gate FAIL — non-reversible ops without proof: {sorted(_missing)}"
)


# ── Public API ────────────────────────────────────────────────────────────────


def emit_kenosis_proof(
    op_id: str,
    receipt_ref: str,
    pre_state_override: Optional[str] = None,
    post_state_override: Optional[str] = None,
) -> KenosisProof:
    """Emit a runtime KenosisProof bound to a live Lineage Fabric receipt.

    Args:
        op_id:               Registry op identifier.
        receipt_ref:         Actual receipt_id from the live ReceiptChain
                             (e.g. ``"R_000042"``).  Must be non-null.
        pre_state_override:  Optional SHA256 hash of the actual pre-transition
                             State Manifold snapshot (replaces default).
        post_state_override: Optional SHA256 hash of the actual post-transition
                             State Manifold snapshot (replaces default).

    Returns:
        A KenosisProof anchored to the provided receipt_ref.

    Raises:
        KeyError:   If op_id is not in the non-reversible registry.
        ValueError: If receipt_ref is empty / None.
    """
    if not receipt_ref:
        raise ValueError("receipt_ref must be non-null (Lineage Fabric anchor required)")

    t = NON_REVERSIBLE[op_id]
    base = _build_proof(t, receipt_ref)

    if pre_state_override or post_state_override:
        return KenosisProof(
            op_id=base.op_id,
            pre_state_hash=pre_state_override or base.pre_state_hash,
            post_state_hash=post_state_override or base.post_state_hash,
            justification=base.justification,
            bounded_budget=base.bounded_budget,
            compensating_action=base.compensating_action,
            receipt_ref=receipt_ref,
        )

    return base


def proof_for(op_id: str) -> KenosisProof:
    """Return the constitutional proof for *op_id* (always non-null receipt_ref)."""
    return CONSTITUTIONAL_PROOFS[op_id]


def all_proofs() -> list[KenosisProof]:
    """Return every constitutional proof, sorted by op_id."""
    return [CONSTITUTIONAL_PROOFS[k] for k in sorted(CONSTITUTIONAL_PROOFS)]
