"""Hard-gate activation gate.

Soak: ≥30 days of receipts + ≥4 weekly audits passed + classifier accuracy
≥0.97 + false_control_rate ≤0.02. Production has a real 30-day clock; CI uses
synthetic timestamp-shifted fixtures.
"""
from __future__ import annotations
import json, pathlib
from datetime import datetime, timedelta, timezone
from typing import List

def soak_satisfied(receipts: List[dict], now: datetime | None = None) -> bool:
    if not receipts: return False
    now = now or datetime.now(tz=timezone.utc)
    earliest = min(datetime.fromisoformat(r["timestamp"].replace("Z","+00:00")) for r in receipts)
    return (now - earliest) >= timedelta(days=30)

def audits_passed(audits: List[dict], n: int = 4) -> bool:
    passed = [a for a in audits if a.get("passed")]
    return len(passed) >= n

def gate_open(*, receipts: List[dict], audits: List[dict],
              accuracy: float, false_control_rate: float,
              now: datetime | None = None) -> bool:
    return (soak_satisfied(receipts, now) and audits_passed(audits)
            and accuracy >= 0.97 and false_control_rate <= 0.02)
