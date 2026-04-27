"""30-day timestamp-shifted synthetic receipts so CI can replay canon-promotion."""
from __future__ import annotations
import json, pathlib, hashlib
from datetime import datetime, timedelta, timezone

SEED = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
GENESIS = "0"*64

def _canon(d: dict) -> bytes:
    return json.dumps(d, sort_keys=True, separators=(",",":")).encode()

def build_30_days(out: pathlib.Path) -> list[dict]:
    receipts = []
    prev = GENESIS
    for day in range(30):
        ts = SEED + timedelta(days=day)
        for hr in (9, 13, 17):  # 3 receipts/day
            ts2 = ts + timedelta(hours=hr)
            r = {
                "receipt_id": f"rcp_d{day:02d}h{hr:02d}",
                "timestamp":  ts2.isoformat(),
                "kind":       "ALET_DAILY_CONTROL_SUMMARY",
                "prev_hash":  prev,
                "payload":    {"day": day, "hour": hr, "ok": True,
                                "control_ratio": 0.86 + 0.01*(day%3),
                                "concern_leakage": 0.03,
                                "false_control_rate": 0.01,
                                "feedback_integrity": 0.96},
            }
            r["receipt_hash"] = hashlib.sha256(b"\x00"+_canon(r)).hexdigest()
            receipts.append(r); prev = r["receipt_hash"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(r, sort_keys=True) for r in receipts) + "\n")
    return receipts

if __name__ == "__main__":
    p = pathlib.Path(__file__).parent / "aletheia_control_30day.jsonl"
    rs = build_30_days(p)
    print(f"wrote {len(rs)} receipts to {p}")
