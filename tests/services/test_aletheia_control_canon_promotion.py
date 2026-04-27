"""30-day fixture-based canon promotion path."""
import json, pathlib
from services.aletheia_control.enforce import gate_open
from datetime import datetime, timedelta, timezone

FIX = pathlib.Path("tests/fixtures/aletheia_control_30day.jsonl")

def test_fixture_exists_and_has_90_receipts():
    assert FIX.exists()
    lines = FIX.read_text().splitlines()
    assert len(lines) == 90

def test_canon_promotion_gate_open_after_30_days():
    receipts = [json.loads(ln) for ln in FIX.read_text().splitlines()]
    audits = [{"passed":True}]*4
    now = datetime(2026,2,15,tzinfo=timezone.utc)
    assert gate_open(receipts=receipts, audits=audits, accuracy=0.974, false_control_rate=0.01, now=now)
