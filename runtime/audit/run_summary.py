from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict


def write_run_summary(run_dir: str | Path, summary: Dict[str, Any]) -> Path:
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "run_summary.json"

    payload = {
        "schema_version": "v1",
        "run_id": summary.get("run_id"),
        "task_id": summary.get("task_id"),
        "started_ts_ms": summary.get("started_ts_ms"),
        "finished_ts_ms": int(time.time() * 1000),
        "duration_ms": summary.get("duration_ms"),
        "ok": summary.get("ok", False),
        "intent": summary.get("intent"),
        "task_type": summary.get("task_type"),
        "execution_mode": summary.get("execution_mode"),
        "policy_version": "v1",
        "policy_hash": summary.get("policy_hash"),
        "services": summary.get("services", {}),
        "mounts": summary.get("mounts", {}),
        "checks": summary.get("checks", {}),
        "failure_reason": summary.get("failure_reason"),
        "artifact_refs": summary.get("artifact_refs", []),
        "event_count": summary.get("event_count", 0),
        "contradictions": summary.get("contradictions", []),
    }

    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
