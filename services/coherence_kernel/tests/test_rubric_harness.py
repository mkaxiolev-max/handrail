"""Gate P5 — Rubric harness 7-night trajectory acceptance test.

REQUIRE:
  Frozen corpus (seed=42) loads 100 branches
  Each branch has score_100 deterministic across runs
  Aggregate score >= 95.0 for all 7 simulated nights
  100% of corpus branches score >= 78.0 (target_threshold)
  Trajectory JSONL appended correctly
  Scores are deterministic (same corpus → same scores on repeat)
"""
from __future__ import annotations
import json, tempfile
from pathlib import Path
import pytest
from services.coherence_kernel.harness.corpus import load_corpus, CORPUS_PATH
from services.coherence_kernel.harness.run_rubric import run_night
from services.coherence_kernel.harness.trajectory import run_trajectory, load_trajectory

REQUIRED_AGGREGATE = 95.0
REQUIRED_THRESHOLD_PCT = 100.0  # 100% of corpus branches must clear 78.0
N_NIGHTS = 7


@pytest.fixture(autouse=True)
def _isolated_ledger(tmp_path):
    from services.coherence_kernel.storage import ledger
    db = tmp_path / "harness_test.db"
    ledger.get_conn(db)
    yield db
    ledger.close_conn(db)


def test_corpus_loads_100_branches():
    branches = load_corpus()
    assert len(branches) == 100


def test_corpus_all_have_required_fields():
    branches = load_corpus()
    for b in branches:
        assert b.id.startswith("corpus_s42_")
        assert b.evidence_amplitude.magnitude >= 0.9
        assert b.evidence_amplitude.source_diversity >= 0.88
        assert len(b.cps_op_chain) >= 4
        assert len(b.contradiction_links) >= 4


def test_single_night_aggregate(_isolated_ledger):
    report = run_night(0, db_path=_isolated_ledger)
    assert report["n_branches"] == 100
    assert report["aggregate_score"] >= REQUIRED_AGGREGATE, (
        f"night 0 aggregate={report['aggregate_score']:.4f} < {REQUIRED_AGGREGATE}"
    )


def test_single_night_threshold_pct(_isolated_ledger):
    report = run_night(0, db_path=_isolated_ledger)
    assert report["pct_above_threshold"] >= REQUIRED_THRESHOLD_PCT, (
        f"only {report['pct_above_threshold']}% branches cleared 78.0"
    )


def test_7_night_trajectory(_isolated_ledger):
    """All 7 nights must produce aggregate >= 95.0."""
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        traj_path = Path(f.name)

    reports = run_trajectory(
        n_nights=N_NIGHTS, db_path=_isolated_ledger, output_path=traj_path
    )
    assert len(reports) == N_NIGHTS

    for r in reports:
        assert r["aggregate_score"] >= REQUIRED_AGGREGATE, (
            f"night {r['night']} aggregate={r['aggregate_score']:.4f} < {REQUIRED_AGGREGATE}"
        )
        assert r["pct_above_threshold"] >= REQUIRED_THRESHOLD_PCT

    traj_path.unlink(missing_ok=True)


def test_trajectory_jsonl_written(_isolated_ledger):
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        traj_path = Path(f.name)

    run_trajectory(n_nights=3, db_path=_isolated_ledger, output_path=traj_path)
    loaded = load_trajectory(traj_path)
    assert len(loaded) == 3
    for r in loaded:
        assert "aggregate_score" in r
        assert "night" in r
    traj_path.unlink(missing_ok=True)


def test_determinism_across_runs(_isolated_ledger):
    """Same corpus → identical aggregate score on two independent runs."""
    r1 = run_night(0, db_path=_isolated_ledger)
    r2 = run_night(0, db_path=_isolated_ledger)
    assert r1["aggregate_score"] == r2["aggregate_score"]


def test_score_monotone_nights(_isolated_ledger):
    """Scores should not degrade night-to-night (frozen corpus → identical each night)."""
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        traj_path = Path(f.name)

    reports = run_trajectory(n_nights=N_NIGHTS, db_path=_isolated_ledger, output_path=traj_path)
    aggregates = [r["aggregate_score"] for r in reports]
    # All nights should be equal (deterministic corpus)
    assert len(set(aggregates)) == 1, f"scores unexpectedly varied: {aggregates}"
    traj_path.unlink(missing_ok=True)
