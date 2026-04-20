"""Q15 — Apollo tests."""
from services.apollo import EvidenceTelemetry, downgrade_factor, adjusted

def test_no_gap_no_downgrade():
    t = EvidenceTelemetry(0.85, 0.85, True)
    assert downgrade_factor(t) == 1.0
    assert adjusted(92.0, t) == 92.0

def test_overclaim_downgrades():
    t = EvidenceTelemetry(0.99, 0.60, True)
    assert downgrade_factor(t) < 0.5
    assert adjusted(90.0, t) < 50.0

def test_missing_receipts_penalize():
    t = EvidenceTelemetry(0.80, 0.80, False)
    assert downgrade_factor(t) == 0.8
