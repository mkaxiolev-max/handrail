from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_event(run_dir: str | Path, event_type: str, payload: Dict[str, Any]) -> Path:
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = run_dir / "proof_ledger.jsonl"
    event = {
        "ts": now_utc_iso(),
        "event_type": event_type,
        "payload": payload,
    }
    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")
    return ledger_path
