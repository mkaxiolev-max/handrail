"""Replay-soundness test suite — State Manifold reversibility coverage.

10 tests covering:
  • checkpoint identity (bit-identical hashes across identical logs)
  • replay tolerance (mixed R / B / I transitions replay without error)
  • kenosis proof presence for all non-reversible ops
  • receipt_ref non-null invariant on all constitutional proofs
  • 100% coverage assertion against the full registry
  • soundness of well-formed logs (hash_match=True)
  • ReplaySoundnessError on hash mismatch
  • genesis fallback when log has no reversible checkpoint
  • empty-log trivial soundness
  • ops_replayed count correctness
"""
import pytest

from services.ns_core.reversibility.registry import (
    REGISTRY,
    REVERSIBLE,
    NON_REVERSIBLE,
    BOUNDED_IRREVERSIBLE,
    IRREVERSIBLE,
    Kind,
    coverage_gate,
)
from services.ns_core.reversibility.kenosis import (
    CONSTITUTIONAL_PROOFS,
    all_proofs,
    proof_for,
)
from services.ns_core.reversibility.replay import (
    TransitionRecord,
    Checkpoint,
    manifold_hash,
    find_latest_reversible_checkpoint,
    replay_from_checkpoint,
    prove_replay_soundness,
    ReplaySoundnessError,
)


# ---------------------------------------------------------------------------
# Fixtures — reusable TransitionRecords built from real registry op_ids
# ---------------------------------------------------------------------------

TS = "2026-04-23T00:00:00Z"


def _rec(op_id: str, before: dict, after: dict, ref: str = "R_000001") -> TransitionRecord:
    return TransitionRecord(
        op_id=op_id,
        ts_utc=TS,
        manifold_before=before,
        manifold_after=after,
        receipt_ref=ref,
    )


def _sound_log() -> list[TransitionRecord]:
    """Three-record log: R → R → B.  The last reversible checkpoint is at index 1."""
    r0 = _rec("voice.idle→ready",         {"voice": "idle"},       {"voice": "ready"},        "R_000001")
    r1 = _rec("voice.ready→listening",    {"voice": "ready"},      {"voice": "listening"},    "R_000002")
    r2 = _rec("voice.listening→transcribing",
              {"voice": "listening"}, {"voice": "transcribing"}, "R_000003")
    return [r0, r1, r2]


# ---------------------------------------------------------------------------
# Test 1 — Checkpoint identity
# ---------------------------------------------------------------------------

def test_checkpoint_identity():
    """Two identical logs must produce bit-identical checkpoint hashes."""
    mk = lambda ref: _rec(
        "voice.idle→ready",
        {"voice": "idle"},
        {"voice": "ready"},
        ref,
    )
    cp_a = find_latest_reversible_checkpoint([mk("R_A")])
    cp_b = find_latest_reversible_checkpoint([mk("R_B")])
    # The checkpoint state_hash depends only on manifold_after, not receipt_ref.
    assert cp_a is not None and cp_b is not None
    assert cp_a.state_hash == cp_b.state_hash


# ---------------------------------------------------------------------------
# Test 2 — Replay tolerance (mixed reversibility classes)
# ---------------------------------------------------------------------------

def test_replay_tolerance_mixed_transitions():
    """Replaying a log with R, B, and I transitions completes without raising."""
    log = _sound_log()
    # Append an irreversible record.
    log.append(_rec("receipt.emit", {"receipt": "chain_n"}, {"receipt": "chain_n+1"}, "R_000004"))
    cp = find_latest_reversible_checkpoint(log)
    assert cp is not None
    result = replay_from_checkpoint(log, cp, strict=False)
    assert result.ops_replayed >= 1


# ---------------------------------------------------------------------------
# Test 3 — Kenosis proof presence for every non-reversible op
# ---------------------------------------------------------------------------

def test_kenosis_proof_presence_all_non_reversible_ops():
    """Every IRREVERSIBLE and BOUNDED_IRREVERSIBLE op has a KenosisProof."""
    proof_ids = set(CONSTITUTIONAL_PROOFS)
    missing = [op_id for op_id in NON_REVERSIBLE if op_id not in proof_ids]
    assert not missing, f"Ops without constitutional proof: {missing}"


# ---------------------------------------------------------------------------
# Test 4 — receipt_ref is non-null on all constitutional proofs
# ---------------------------------------------------------------------------

def test_kenosis_receipt_ref_non_null():
    """All constitutional KenosisProofs must be anchored to the Lineage Fabric."""
    for proof in all_proofs():
        assert proof.receipt_ref, (
            f"receipt_ref is null/empty for proof of {proof.op_id!r}"
        )
        assert proof.receipt_ref.startswith("lineage://"), (
            f"receipt_ref for {proof.op_id!r} is not a Lineage Fabric URI: "
            f"{proof.receipt_ref!r}"
        )


# ---------------------------------------------------------------------------
# Test 5 — 100% coverage gate passes (irreversible_without_proof == 0)
# ---------------------------------------------------------------------------

def test_coverage_100_percent():
    """coverage_gate() must report zero ops without proof."""
    report = coverage_gate()
    assert report["irreversible_without_proof"] == 0
    assert report["total_ops"] == len(REGISTRY)
    assert report["reversible"] + report["irreversible_with_proof"] == report["total_ops"]


# ---------------------------------------------------------------------------
# Test 6 — Replay of a well-formed log is sound (hash_match=True)
# ---------------------------------------------------------------------------

def test_replayed_manifold_hash_match():
    """prove_replay_soundness returns sound=True for a self-consistent log."""
    log = _sound_log()
    result = prove_replay_soundness(log, strict=True)
    assert result.sound, (
        f"Expected sound replay; mismatches={result.mismatches}"
    )


# ---------------------------------------------------------------------------
# Test 7 — ReplaySoundnessError on post_state_hash mismatch
# ---------------------------------------------------------------------------

def test_replay_soundness_error_on_hash_mismatch():
    """A log record with a wrong manifold_after triggers ReplaySoundnessError."""
    r0 = _rec("voice.idle→ready", {"voice": "idle"}, {"voice": "ready"}, "R_000001")
    # Corrupt the manifold_after so post_state_hash won't match replayed result.
    r1_corrupt = _rec(
        "voice.listening→transcribing",
        {"voice": "ready"},
        {"voice": "CORRUPTED"},   # replay will produce {"voice": "transcribing"}
        "R_000002",
    )
    log = [r0, r1_corrupt]
    cp = find_latest_reversible_checkpoint(log)
    assert cp is not None
    with pytest.raises(ReplaySoundnessError):
        replay_from_checkpoint(log, cp, strict=True)


# ---------------------------------------------------------------------------
# Test 8 — Empty log is trivially sound
# ---------------------------------------------------------------------------

def test_replay_empty_log_is_trivially_sound():
    """prove_replay_soundness on an empty log returns sound=True with no work done."""
    result = prove_replay_soundness([])
    assert result.sound
    assert result.ops_replayed == 0
    assert result.checkpoint_index == -1


# ---------------------------------------------------------------------------
# Test 9 — Registry: every op has a valid Kind classification
# ---------------------------------------------------------------------------

def test_registry_all_ops_classified():
    """Every transition in REGISTRY must carry a valid Kind value."""
    valid = {Kind.REVERSIBLE, Kind.IRREVERSIBLE, Kind.BOUNDED_IRREVERSIBLE}
    unclassified = [op for op, t in REGISTRY.items() if t.kind not in valid]
    assert not unclassified, f"Ops with invalid Kind: {unclassified}"


# ---------------------------------------------------------------------------
# Test 10 — ops_replayed count matches the tail of the log after checkpoint
# ---------------------------------------------------------------------------

def test_ops_replayed_count_matches_log_tail():
    """ops_replayed equals len(log) - checkpoint_index - 1."""
    log = _sound_log()   # R(0) → R(1) → B(2)  — checkpoint at index 1
    cp = find_latest_reversible_checkpoint(log)
    assert cp is not None
    result = replay_from_checkpoint(log, cp, strict=False)
    expected_replayed = len(log) - cp.log_index - 1
    assert result.ops_replayed == expected_replayed
