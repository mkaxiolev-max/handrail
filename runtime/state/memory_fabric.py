from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_snapshot(run_dir: str | Path, snapshot: Dict[str, Any]) -> Path:
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "memory_fabric_snapshot.json"
    payload = {
        "ts": now_utc_iso(),
        "snapshot": snapshot,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
