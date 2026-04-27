"""Hard-gate enforcement when ALETHEIA_CONTROL_ENFORCE=1."""
from services.aletheia_control.enforce import gate_open, soak_satisfied, audits_passed
from datetime import datetime, timedelta, timezone

def test_soak_30days_required():
    now = datetime(2026,2,15,tzinfo=timezone.utc)
    fresh = [{"timestamp":"2026-02-10T00:00:00+00:00"}]
    assert soak_satisfied(fresh, now) is False
    aged = [{"timestamp":"2026-01-01T00:00:00+00:00"}]
    assert soak_satisfied(aged, now) is True

def test_audits_4_required():
    assert audits_passed([{"passed":True}]*3) is False
    assert audits_passed([{"passed":True}]*4) is True

def test_gate_open_all_conditions():
    now = datetime(2026,2,15,tzinfo=timezone.utc)
    aged = [{"timestamp":"2026-01-01T00:00:00+00:00"}]
    audits = [{"passed":True}]*4
    assert gate_open(receipts=aged, audits=audits, accuracy=0.97, false_control_rate=0.02, now=now)
    assert not gate_open(receipts=aged, audits=audits, accuracy=0.96, false_control_rate=0.02, now=now)
    assert not gate_open(receipts=aged, audits=audits, accuracy=0.97, false_control_rate=0.03, now=now)
