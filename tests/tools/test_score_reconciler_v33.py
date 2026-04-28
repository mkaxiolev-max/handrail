"""C24 — Score reconciler v3.3 + I8 tests. I8."""
import pytest
from tools.score_reconciler_v33 import ScoreReconcilerV33, WEIGHTS_V33, ReconcilerReport


def test_weights_sum_to_one():
    assert abs(sum(WEIGHTS_V33.values()) - 1.0) < 1e-9


def test_i8_in_weights():
    assert "I8" in WEIGHTS_V33
    assert WEIGHTS_V33["I8"] == 0.10


def test_reconcile_all_zero():
    r = ScoreReconcilerV33()
    report = r.reconcile()
    assert report.composite == 0.0


def test_reconcile_all_100():
    r = ScoreReconcilerV33()
    for inst in WEIGHTS_V33:
        r.set_instrument(inst, 100.0)
    report = r.reconcile()
    assert abs(report.composite - 100.0) < 0.01


def test_band_classification():
    r = ScoreReconcilerV33()
    for inst in WEIGHTS_V33:
        r.set_instrument(inst, 95.0)
    report = r.reconcile()
    assert report.band == "external_certification_ready"


def test_unknown_instrument_raises():
    r = ScoreReconcilerV33()
    with pytest.raises(ValueError):
        r.set_instrument("I99", 50.0)


def test_i8_contribution_tracked():
    r = ScoreReconcilerV33()
    r.set_instrument("I8", 80.0)
    report = r.reconcile()
    assert report.i8_contribution > 0


def test_to_dict_structure():
    r = ScoreReconcilerV33()
    d = r.to_dict()
    assert "composite" in d
    assert "instruments" in d
    assert "I8" in d["instruments"]


def test_export(tmp_path):
    r = ScoreReconcilerV33()
    r.set_instrument("I7", 90.0)
    out = r.export(tmp_path / "score.json")
    assert out.exists()
    import json
    data = json.loads(out.read_text())
    assert data["version"] == "v3.3"
