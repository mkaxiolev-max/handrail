"""Replay-soundness prover for the NS∞ State Manifold.

Given a log of TransitionRecords, this module:
  1. Reconstructs the State Manifold up to the latest reversible checkpoint.
  2. Verifies that replayed manifold hashes are bit-identical to the recorded
     post_state_hash values.
  3. Raises ReplaySoundnessError if any discrepancy is detected.

Terminology
-----------
State Manifold : The union of all domain states at a point in time.
                 Represented as dict[domain, current_state_value].
Checkpoint     : A TransitionRecord whose op is REVERSIBLE — the manifold
                 snapshot at this point is a safe rollback anchor.
Replay         : Re-applying the forward transition function from a checkpoint
                 to reconstruct subsequent manifold states deterministically.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional

from .registry import REGISTRY, Kind, StateTransition


# ── Manifold hashing ──────────────────────────────────────────────────────────


def manifold_hash(manifold: dict[str, str]) -> str:
    """Canonical SHA256 hash of the State Manifold snapshot.

    The hash is computed over a JSON-serialised dict sorted by key, so
    it is deterministic regardless of insertion order.
    """
    payload = json.dumps(manifold, sort_keys=True)
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()


# ── Data structures ───────────────────────────────────────────────────────────


@dataclass
class TransitionRecord:
    """A single transition event in the State Manifold log.

    Attributes:
        op_id:            Registry op identifier (must exist in REGISTRY).
        ts_utc:           ISO-8601 UTC timestamp of the transition.
        manifold_before:  Domain-state snapshot immediately before the op.
        manifold_after:   Domain-state snapshot immediately after the op.
        receipt_ref:      Lineage Fabric receipt_id anchoring this record.
        pre_state_hash:   SHA256 hash of manifold_before (recorded by emitter).
        post_state_hash:  SHA256 hash of manifold_after (recorded by emitter).
    """
    op_id: str
    ts_utc: str
    manifold_before: dict[str, str]
    manifold_after: dict[str, str]
    receipt_ref: str
    pre_state_hash: str = field(init=False)
    post_state_hash: str = field(init=False)

    def __post_init__(self) -> None:
        self.pre_state_hash = manifold_hash(self.manifold_before)
        self.post_state_hash = manifold_hash(self.manifold_after)

    @property
    def kind(self) -> Optional[Kind]:
        t = REGISTRY.get(self.op_id)
        return t.kind if t else None

    @property
    def is_reversible(self) -> bool:
        return self.kind == Kind.REVERSIBLE

    @property
    def transition(self) -> Optional[StateTransition]:
        return REGISTRY.get(self.op_id)


@dataclass
class Checkpoint:
    """A safe rollback anchor in the transition log.

    Attributes:
        log_index:   Index of the TransitionRecord in the log.
        manifold:    State Manifold snapshot at this checkpoint.
        state_hash:  Canonical hash of *manifold* (bit-identity anchor).
        receipt_ref: Lineage Fabric receipt_id of the anchoring transition.
    """
    log_index: int
    manifold: dict[str, str]
    state_hash: str
    receipt_ref: str


@dataclass
class ReplayResult:
    """Output of a replay-soundness proof run.

    Attributes:
        checkpoint_index:    Log index of the checkpoint used.
        checkpoint_hash:     Hash of the checkpoint manifold.
        replayed_manifold:   Final reconstructed manifold.
        replayed_hash:       Hash of the replayed manifold.
        hash_match:          True iff replayed_hash equals the last recorded
                             post_state_hash in the log segment.
        ops_replayed:        Number of transitions replayed from the checkpoint.
        mismatches:          List of (op_index, op_id, expected, actual) tuples
                             where replay diverged from the recorded hash.
    """
    checkpoint_index: int
    checkpoint_hash: str
    replayed_manifold: dict[str, str]
    replayed_hash: str
    hash_match: bool
    ops_replayed: int
    mismatches: list[tuple[int, str, str, str]] = field(default_factory=list)

    @property
    def sound(self) -> bool:
        return self.hash_match and not self.mismatches


class ReplaySoundnessError(RuntimeError):
    """Raised when replay produces a hash that does not match the recorded value."""


# ── Core prover functions ─────────────────────────────────────────────────────


def find_latest_reversible_checkpoint(log: list[TransitionRecord]) -> Optional[Checkpoint]:
    """Scan backward through *log* and return the latest reversible checkpoint.

    A checkpoint is any TransitionRecord whose op is classified REVERSIBLE in
    the registry.  The checkpoint manifold is the *manifold_after* snapshot of
    that record, representing the State Manifold immediately after a safe op.

    Returns None if the log contains no reversible transitions.
    """
    for i in range(len(log) - 1, -1, -1):
        rec = log[i]
        if rec.is_reversible:
            snap = dict(rec.manifold_after)
            return Checkpoint(
                log_index=i,
                manifold=snap,
                state_hash=manifold_hash(snap),
                receipt_ref=rec.receipt_ref,
            )
    return None


def _apply_transition(manifold: dict[str, str], record: TransitionRecord) -> dict[str, str]:
    """Apply a single transition to *manifold*, returning the updated copy.

    The transition updates the domain named in the registry entry for op_id.
    If the op_id is not in the registry, the manifold is returned unchanged
    (unknown ops are treated as identity).
    """
    t = record.transition
    if t is None:
        return dict(manifold)
    updated = dict(manifold)
    updated[t.domain] = t.to_state
    return updated


def replay_from_checkpoint(
    log: list[TransitionRecord],
    checkpoint: Checkpoint,
    *,
    strict: bool = True,
) -> ReplayResult:
    """Replay transitions from *checkpoint* to the end of *log*.

    For each transition after the checkpoint, the replayed manifold hash is
    compared against the recorded post_state_hash.

    Args:
        log:        Full transition log.
        checkpoint: Starting anchor returned by find_latest_reversible_checkpoint.
        strict:     If True (default), raise ReplaySoundnessError on the first
                    hash mismatch.  If False, collect all mismatches and return.

    Returns:
        ReplayResult describing the outcome of the proof run.

    Raises:
        ReplaySoundnessError: When strict=True and any hash mismatch is detected.
    """
    manifold = dict(checkpoint.manifold)
    mismatches: list[tuple[int, str, str, str]] = []
    ops_replayed = 0

    for i in range(checkpoint.log_index + 1, len(log)):
        rec = log[i]
        manifold = _apply_transition(manifold, rec)
        ops_replayed += 1
        replayed = manifold_hash(manifold)

        if replayed != rec.post_state_hash:
            mismatches.append((i, rec.op_id, rec.post_state_hash, replayed))
            if strict:
                raise ReplaySoundnessError(
                    f"Replay hash mismatch at log[{i}] op={rec.op_id!r}: "
                    f"expected={rec.post_state_hash} got={replayed}"
                )

    final_hash = manifold_hash(manifold)
    recorded_final = log[-1].post_state_hash if log else ""

    return ReplayResult(
        checkpoint_index=checkpoint.log_index,
        checkpoint_hash=checkpoint.state_hash,
        replayed_manifold=dict(manifold),
        replayed_hash=final_hash,
        hash_match=(final_hash == recorded_final) if log else True,
        ops_replayed=ops_replayed,
        mismatches=mismatches,
    )


def prove_replay_soundness(
    log: list[TransitionRecord],
    *,
    strict: bool = True,
) -> ReplayResult:
    """Top-level entry point: find the latest checkpoint and replay to end of log.

    If the log is empty, returns a trivially sound result.

    Args:
        log:    Ordered list of TransitionRecords representing the State Manifold
                history.
        strict: Passed through to replay_from_checkpoint.

    Returns:
        ReplayResult. Check `.sound` for the final verdict.

    Raises:
        ReplaySoundnessError: When strict=True and replay diverges.
    """
    if not log:
        return ReplayResult(
            checkpoint_index=-1,
            checkpoint_hash="",
            replayed_manifold={},
            replayed_hash="",
            hash_match=True,
            ops_replayed=0,
        )

    checkpoint = find_latest_reversible_checkpoint(log)

    if checkpoint is None:
        # No reversible checkpoint in log — replay from the very beginning.
        first = log[0]
        initial_manifold = dict(first.manifold_before)
        checkpoint = Checkpoint(
            log_index=-1,
            manifold=initial_manifold,
            state_hash=manifold_hash(initial_manifold),
            receipt_ref=first.receipt_ref,
        )

    return replay_from_checkpoint(log, checkpoint, strict=strict)
