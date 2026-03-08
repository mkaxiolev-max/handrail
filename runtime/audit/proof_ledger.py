from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def now_ts_ms() -> int:
    return int(time.time() * 1000)


def now_mono_ns() -> int:
    return time.monotonic_ns()


def _next_seq(run_dir: Path) -> int:
    seq_path = run_dir / ".seq"
    if seq_path.exists():
        try:
            current = int(seq_path.read_text().strip())
        except Exception:
            current = 0
    else:
        current = 0
    nxt = current + 1
    seq_path.write_text(str(nxt))
    return nxt


def append_event(
    run_dir: str | Path,
    event_type: str,
    payload: Dict[str, Any],
    *,
    service: str = "ns",
    layer: str = "ledger",
    status: str = "ok",
    message: str = "",
    parent_event_id: str | None = None,
) -> Path:
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    seq = _next_seq(run_dir)
    event_id = f"evt_{seq:06d}"

    ledger_path = run_dir / "proof_ledger.jsonl"
    event = {
        "schema_version": "v1",
        "run_id": payload.get("run_id"),
        "task_id": payload.get("task_id"),
        "event_id": event_id,
        "parent_event_id": parent_event_id,
        "seq": seq,
        "ts_ms": now_ts_ms(),
        "mono_ns": now_mono_ns(),
        "service": service,
        "layer": layer,
        "event_type": event_type,
        "status": status,
        "policy_hash": payload.get("policy_hash"),
        "message": message or event_type,
        "data": payload,
    }

    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")

    return ledger_path
