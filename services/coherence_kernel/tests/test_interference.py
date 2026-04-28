"""Phase 1 acceptance: interference quality >= 0.85 mean; deterministic across 3 runs."""
from __future__ import annotations
import json, random, statistics
from pathlib import Path

import pytest
from services.coherence_kernel import schemas
from services.coherence_kernel.interference import interference_pass

_FIXTURES = Path(__file__).parent / "fixtures"
_SEED = 42


def _load_pairs(fname: str) -> list[tuple[schemas.BranchState, schemas.BranchState, str]]:
    pairs = []
    for line in (_FIXTURES / fname).read_text().splitlines():
        d = json.loads(line)
        pairs.append((
            schemas.BranchState(**d["a"]),
            schemas.BranchState(**d["b"]),
            d["expected"],
        ))
    return pairs


@pytest.fixture(scope="module")
def contra_pairs():
    return _load_pairs("pairs_500_contra.jsonl")


@pytest.fixture(scope="module")
def reinforce_pairs():
    return _load_pairs("pairs_500_reinforce.jsonl")


def test_interference_quality_mean_contra(contra_pairs):
    scores = [interference_pass(a, b).interference_quality_score for a, b, _ in contra_pairs]
    mean_score = statistics.mean(scores)
    assert mean_score >= 0.85, f"contra mean={mean_score:.4f} < 0.85"


def test_interference_quality_mean_reinforce(reinforce_pairs):
    scores = [interference_pass(a, b).interference_quality_score for a, b, _ in reinforce_pairs]
    mean_score = statistics.mean(scores)
    assert mean_score >= 0.85, f"reinforce mean={mean_score:.4f} < 0.85"


def test_interference_deterministic():
    """Three runs with fixed seed produce identical results."""
    pairs = _load_pairs("pairs_500_contra.jsonl")[:50] + _load_pairs("pairs_500_reinforce.jsonl")[:50]
    results = []
    for _ in range(3):
        run = [interference_pass(a, b).interference_quality_score for a, b, _ in pairs]
        results.append(run)
    assert results[0] == results[1] == results[2], "non-deterministic interference output"


def test_ops_registered_exactly():
    from services.coherence_kernel.interference import COMPARISON_OPS
    expected = {
        "semantic_overlap", "claim_polarity", "provenance_intersection",
        "evidence_amplitude_phase", "contradiction_pressure",
    }
    assert set(COMPARISON_OPS) == expected
    assert len(COMPARISON_OPS) == 5


def test_receipt_written_to_ledger():
    from services.coherence_kernel.storage import ledger
    pairs = _load_pairs("pairs_500_contra.jsonl")[:1]
    a, b, _ = pairs[0]
    result = interference_pass(a, b)
    assert result.receipt.startswith("IFP-")
    # verify ledger has this receipt
    import sqlite3
    conn = ledger.get_conn()
    row = conn.execute(
        "SELECT receipt FROM interference_pass WHERE receipt=?", (result.receipt,)
    ).fetchone()
    assert row is not None, f"receipt {result.receipt} not in ledger"
