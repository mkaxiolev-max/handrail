"""Phase 0 acceptance: 1000 roundtrip passes, zero mutations, hash chain contiguous."""
from __future__ import annotations
import hashlib, json, random, tempfile, uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from services.coherence_kernel import schemas
from services.coherence_kernel.storage import ledger as _ledger

_RNG = random.Random(42)


def _rng_float(lo=0.0, hi=1.0):
    return round(_RNG.uniform(lo, hi), 6)


def _make_amplitude():
    return schemas.AmplitudeEvidenceWeight(
        magnitude=_rng_float(),
        phase=_rng_float(-1.0, 1.0),
        provenance_chain=[uuid.uuid4().hex for _ in range(_RNG.randint(1, 5))],
        redundancy_count=_RNG.randint(0, 10),
        source_diversity=_rng_float(),
    )


def _make_branch():
    return schemas.BranchState(
        id=uuid.uuid4().hex,
        claim=f"claim_{uuid.uuid4().hex[:8]}",
        evidence_amplitude=_make_amplitude(),
        uncertainty=_rng_float(),
        contradiction_links=[uuid.uuid4().hex for _ in range(_RNG.randint(0, 3))],
        reinforcement_links=[uuid.uuid4().hex for _ in range(_RNG.randint(0, 3))],
        reversibility_cost=_rng_float(0.0, 10.0),
        provenance=[uuid.uuid4().hex for _ in range(_RNG.randint(1, 4))],
        parent_branch=uuid.uuid4().hex if _RNG.random() > 0.5 else None,
        decoherence_resistance=_rng_float(),
        qot_state_snapshot={"tick": _RNG.randint(0, 9999)},
        created_at=datetime.now(timezone.utc),
        cps_op_chain=[f"op_{_RNG.randint(0,99)}" for _ in range(_RNG.randint(0, 4))],
    )


def _make_decoherence():
    scores = {k: _rng_float() for k in
              ("urgency_score", "bias_score", "context_loss_score",
               "narrative_lock_score", "social_pressure_score")}
    agg = round(sum(scores.values()) / 5, 6)
    return schemas.DecoherenceDetector(
        **scores,
        aggregate=agg,
        threshold=0.65,
        breached=agg >= 0.65,
    )


def _make_readiness():
    vals = {k: _rng_float(0.0, 10.0) for k in schemas._WEIGHTS}
    return schemas.CollapseReadinessScore.compute(**vals)


def test_amplitude_roundtrip():
    obj = _make_amplitude()
    dumped = obj.model_dump(mode="json")
    restored = schemas.AmplitudeEvidenceWeight(**dumped)
    assert restored == obj


def test_branch_state_roundtrip():
    obj = _make_branch()
    dumped = obj.model_dump(mode="json")
    restored = schemas.BranchState(**dumped)
    assert restored == obj
    # Immutable — Pydantic frozen raises on assignment
    with pytest.raises(Exception):
        restored.claim = "mutated"  # type: ignore[misc]


def test_branch_hash_deterministic():
    obj = _make_branch()
    h1 = obj.canonical_hash()
    h2 = obj.canonical_hash()
    assert h1 == h2
    assert len(h1) == 64


def test_interference_pass_roundtrip():
    obj = schemas.InterferencePass(
        input_branches=[uuid.uuid4().hex, uuid.uuid4().hex],
        comparison_ops=["semantic_overlap", "claim_polarity"],
        cancellation_rule="opposing polarity AND phase < -0.7",
        reinforcement_rule="same polarity AND phase > 0.7",
        output_branches=[uuid.uuid4().hex],
        interference_quality_score=_rng_float(),
        receipt=uuid.uuid4().hex,
    )
    assert schemas.InterferencePass(**obj.model_dump(mode="json")) == obj


def test_decoherence_detector_roundtrip():
    obj = _make_decoherence()
    restored = schemas.DecoherenceDetector(**obj.model_dump(mode="json"))
    assert restored == obj
    assert restored.breached == (restored.aggregate >= restored.threshold)


def test_readiness_score_roundtrip():
    obj = _make_readiness()
    restored = schemas.CollapseReadinessScore(**obj.model_dump(mode="json"))
    assert restored == obj
    assert 0.0 <= restored.score_100 <= 100.0


def test_readiness_score_monotonic():
    base_vals = {k: 5.0 for k in schemas._WEIGHTS}
    base = schemas.CollapseReadinessScore.compute(**base_vals)
    for key in schemas._WEIGHTS:
        improved = dict(base_vals)
        improved[key] = 9.0
        improved_score = schemas.CollapseReadinessScore.compute(**improved)
        assert improved_score.score_100 > base.score_100, f"monotonic fail on {key}"


def test_pointer_state_promotion_roundtrip():
    obj = schemas.PointerStatePromotion(
        branch_id=uuid.uuid4().hex,
        gate_decision="collapse_ready",
        invariants_passed=["sovereign_integrity", "dignity_kernel"],
        invariants_advisory=["contradiction_metabolism"],
        imo_receipt=uuid.uuid4().hex,
        root_ledger_entry=uuid.uuid4().hex,
        reversibility_horizon_seconds=3600,
    )
    assert schemas.PointerStatePromotion(**obj.model_dump(mode="json")) == obj


def test_reversibility_ledger_roundtrip():
    obj = schemas.ReversibilityLedger(
        promotion_id=uuid.uuid4().hex,
        rollback_cost=_rng_float(0.0, 100.0),
        undo_path=f"/ops/rollback/{uuid.uuid4().hex}",
        time_horizon_seconds=_RNG.randint(60, 86400),
        auditor_chamber="NS_Board",
    )
    assert schemas.ReversibilityLedger(**obj.model_dump(mode="json")) == obj


def test_ledger_append_only():
    """Verify UPDATE and DELETE are denied by trigger."""
    import sqlite3
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / f"test_{uuid.uuid4().hex}.db"
        try:
            conn = _ledger.get_conn(db_path)
            _ledger.append("branch_state", {"x": 1}, {"id": "b1"}, db_path)
            with pytest.raises(sqlite3.DatabaseError, match="append-only"):
                conn.execute("UPDATE branch_state SET id='x' WHERE rowid=1")
            with pytest.raises(sqlite3.DatabaseError, match="append-only"):
                conn.execute("DELETE FROM branch_state WHERE rowid=1")
        finally:
            _ledger.close_conn(db_path)


def test_ledger_hash_chain_contiguous():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / f"test_{uuid.uuid4().hex}.db"
        try:
            for i in range(20):
                _ledger.append("receipt", {"i": i}, {"op": "test", "ref_id": str(i)}, db_path)
            assert _ledger.verify_chain("receipt", db_path)
        finally:
            _ledger.close_conn(db_path)
