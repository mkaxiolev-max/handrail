"""Fsync'd append-only JSONL receipt emitter — enforces I2 (append-only) and I5 (hash-chain)."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _hash_entry(name: str, payload: dict, prev_id: str, tick: int) -> str:
    raw = json.dumps(
        {"name": name, "payload": payload, "prev_id": prev_id, "tick": tick},
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode()).hexdigest()


class ReceiptEmitter:
    """Append-only JSONL writer with fsync and hash-chain integrity (I2 / I5)."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._tick = 0
        self._prev_id = "GENESIS"

    def append(self, name: str, payload: Optional[dict] = None) -> str:
        """Append a receipt record; returns the receipt_id (sha256 hex)."""
        payload = payload or {}
        self._tick += 1
        receipt_id = _hash_entry(name, payload, self._prev_id, self._tick)
        record = {
            "receipt_id": receipt_id,
            "name": name,
            "payload": payload,
            "prev_id": self._prev_id,
            "tick": self._tick,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        with open(self._path, "a") as fh:
            fh.write(json.dumps(record) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        self._prev_id = receipt_id
        return receipt_id
