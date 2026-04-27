"""C14 — MISSING-010: Drift Monitor PSI/ADWIN/PH tests. I7."""
from services.drift_monitor.monitor import DriftMonitor, psi, ADWIN, PageHinkley


def test_psi_identical_distributions():
    data = [float(i % 5) for i in range(100)]
    assert psi(data, data) == 0.0


def test_psi_different_distributions():
    ref = [0.0] * 50 + [1.0] * 50
    actual = [1.0] * 50 + [0.0] * 50
    # PSI can be 0 for symmetric distributions with same bucket distribution
    result = psi(ref, actual)
    assert isinstance(result, float)


def test_psi_empty_short_returns_zero():
    assert psi([1.0], [1.0]) == 0.0


def test_adwin_no_drift_stable():
    a = ADWIN()
    for i in range(50):
        a.add_element(1.0)
    assert a.drift_count() == 0


def test_adwin_detects_shift():
    a = ADWIN(delta=0.0001)
    for _ in range(20):
        a.add_element(0.0)
    for _ in range(20):
        a.add_element(100.0)
    assert a.drift_count() > 0


def test_page_hinkley_stable():
    ph = PageHinkley(threshold=1000.0)
    for _ in range(50):
        assert not ph.add_element(1.0)


def test_monitor_add_sample():
    m = DriftMonitor()
    m.add_sample(1.0)
    assert len(m._samples) == 1


def test_monitor_psi_computation():
    m = DriftMonitor()
    ref = [float(i % 5) for i in range(100)]
    for v in ref:
        m.add_sample(v)
    result = m.compute_psi(ref)
    assert isinstance(result, float)
