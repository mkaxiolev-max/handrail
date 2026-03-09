import json
import time
from pathlib import Path


def write_event(run_dir: Path, event_type: str, payload: dict):
    ledger = run_dir / "proof_ledger.jsonl"

    event = {
        "ts_ms": int(time.time() * 1000),
        "event_type": event_type,
        "payload": payload,
    }

    with ledger.open("a") as f:
        f.write(json.dumps(event) + "\n")


def record_boot_event(run_dir: Path, summary: dict):
    write_event(
        run_dir,
        "boot_summary",
        {
            "run_id": summary.get("run_id"),
            "ok": summary.get("ok"),
            "services": summary.get("services"),
            "checks": summary.get("checks"),
        },
    )
