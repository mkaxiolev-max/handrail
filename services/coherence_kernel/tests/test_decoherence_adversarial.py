"""Gate P2: decoherence adversarial acceptance test.

REQUIRE:
  TPR >= 0.95 on 200 high-urgency cases
  FPR <= 0.05 on 200 benign controls
  readiness.score_100 monotonic with sub-metric improvements (property test)
"""
from __future__ import annotations
import json, pathlib, tempfile
from datetime import datetime, timezone
import pytest
from services.coherence_kernel import schemas
from services.coherence_kernel.decoherence import aggregator
from services.coherence_kernel import readiness
from services.coherence_kernel.storage import ledger

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "adversarial_urgency_200.jsonl"


def _load_fixture() -> tuple[list[schemas.BranchState], list[schemas.BranchState]]:
    high, benign = [], []
    for line in FIXTURE.read_text().splitlines():
        rec = json.loads(line)
        branch = schemas.BranchState(**rec["branch"])
        if rec["label"] == "high_urgency":
            high.append(branch)
        else:
            benign.append(branch)
    return high, benign


@pytest.fixture(autouse=True)
def _isolated_ledger(tmp_path):
    db = tmp_path / "ck_adversarial.db"
    ledger.get_conn(db)
    yield
    ledger.close_conn(db)


def test_tpr_high_urgency():
    """Decoherence detector must catch >= 95% of high-urgency branches."""
    high, _ = _load_fixture()
    assert len(high) == 200
    breached = sum(1 for b in high if aggregator.detect(b).breached)
    tpr = breached / len(high)
    assert tpr >= 0.95, f"TPR={tpr:.4f} < 0.95 ({breached}/200 detected)"


def test_fpr_benign_controls():
    """Decoherence detector must not false-alarm on > 5% of benign controls."""
    _, benign = _load_fixture()
    assert len(benign) == 200
    false_positives = sum(1 for b in benign if aggregator.detect(b).breached)
    fpr = false_positives / len(benign)
    assert fpr <= 0.05, f"FPR={fpr:.4f} > 0.05 ({false_positives}/200 false alarms)"


def test_monotonicity_decoherence_resistance(tmp_path):
    """Increasing decoherence_resistance must not decrease readiness.score_100."""
    db = tmp_path / "mono_test.db"
    ledger.get_conn(db)
    try:
        base_amp = schemas.AmplitudeEvidenceWeight(
            magnitude=0.5, phase=0.0,
            provenance_chain=["a", "b", "c"],
            redundancy_count=3, source_diversity=0.5,
        )
        steps = [round(i * 0.1, 1) for i in range(11)]
        scores = []
        for dr in steps:
            b = schemas.BranchState(
                id=f"mono_{dr}",
                claim="monotonicity test",
                evidence_amplitude=base_amp,
                uncertainty=0.4,
                contradiction_links=["c1"],
                reinforcement_links=["r1", "r2"],
                reversibility_cost=3.0,
                decoherence_resistance=dr,
                created_at=datetime.now(timezone.utc),
                cps_op_chain=["op1", "op2"],
            )
            rs = readiness.compute_readiness(b)
            scores.append(rs.score_100)
        for i in range(1, len(scores)):
            assert scores[i] >= scores[i - 1] - 1e-6, (
                f"score_100 decreased at decoherence_resistance step {steps[i]}: "
                f"{scores[i - 1]:.4f} → {scores[i]:.4f}"
            )
    finally:
        ledger.close_conn(db)


def test_monotonicity_magnitude(tmp_path):
    """Increasing evidence magnitude must not decrease readiness.score_100."""
    db = tmp_path / "mono_mag.db"
    ledger.get_conn(db)
    try:
        steps = [round(i * 0.1, 1) for i in range(11)]
        scores = []
        for mag in steps:
            amp = schemas.AmplitudeEvidenceWeight(
                magnitude=mag, phase=0.0,
                provenance_chain=["a", "b", "c"],
                redundancy_count=3, source_diversity=0.5,
            )
            b = schemas.BranchState(
                id=f"monomag_{mag}",
                claim="monotonicity magnitude test",
                evidence_amplitude=amp,
                uncertainty=0.4,
                contradiction_links=["c1"],
                reinforcement_links=["r1", "r2"],
                reversibility_cost=3.0,
                decoherence_resistance=0.5,
                created_at=datetime.now(timezone.utc),
                cps_op_chain=["op1", "op2"],
            )
            rs = readiness.compute_readiness(b)
            scores.append(rs.score_100)
        for i in range(1, len(scores)):
            assert scores[i] >= scores[i - 1] - 1e-6, (
                f"score_100 decreased at magnitude step {steps[i]}: "
                f"{scores[i - 1]:.4f} → {scores[i]:.4f}"
            )
    finally:
        ledger.close_conn(db)


def test_monotonicity_readout_discipline(tmp_path):
    """Decreasing uncertainty must not decrease readiness.score_100."""
    db = tmp_path / "mono_rd.db"
    ledger.get_conn(db)
    try:
        base_amp = schemas.AmplitudeEvidenceWeight(
            magnitude=0.6, phase=0.0,
            provenance_chain=["a", "b", "c"],
            redundancy_count=3, source_diversity=0.6,
        )
        uncertainties = [round(1.0 - i * 0.1, 1) for i in range(11)]
        scores = []
        for u in uncertainties:
            b = schemas.BranchState(
                id=f"monord_{u}",
                claim="monotonicity readout discipline",
                evidence_amplitude=base_amp,
                uncertainty=u,
                contradiction_links=["c1"],
                reinforcement_links=["r1"],
                reversibility_cost=3.0,
                decoherence_resistance=0.5,
                created_at=datetime.now(timezone.utc),
                cps_op_chain=["op1"],
            )
            rs = readiness.compute_readiness(b)
            scores.append(rs.score_100)
        for i in range(1, len(scores)):
            assert scores[i] >= scores[i - 1] - 1e-6, (
                f"score_100 decreased as uncertainty dropped to {uncertainties[i]}: "
                f"{scores[i - 1]:.4f} → {scores[i]:.4f}"
            )
    finally:
        ledger.close_conn(db)


def test_aggregate_bounds():
    """Aggregate decoherence score must always be in [0, 1]."""
    high, benign = _load_fixture()
    for b in high + benign:
        det = aggregator.detect(b)
        assert 0.0 <= det.aggregate <= 1.0, f"aggregate={det.aggregate} out of bounds"


def test_threshold_consistency():
    """breached flag must match aggregate >= threshold for all cases."""
    high, benign = _load_fixture()
    for b in high + benign:
        det = aggregator.detect(b)
        assert det.breached == (det.aggregate >= det.threshold), (
            f"breached mismatch: aggregate={det.aggregate}, threshold={det.threshold}"
        )
