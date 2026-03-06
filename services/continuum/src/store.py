from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

STREAMS = ["legal", "knowledge", "semantic", "operational", "institutional"]

def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

@dataclass
class AppendResult:
    path: Path
    entry_hash: str
    prev_hash: str

class AppendOnlyStore:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        for s in STREAMS:
            (self.data_dir / s).mkdir(parents=True, exist_ok=True)

    def _last_hash_path(self, stream: str) -> Path:
        return self.data_dir / stream / "LAST_HASH"

    def last_hash(self, stream: str) -> str:
        p = self._last_hash_path(stream)
        if not p.exists():
            return "0" * 64
        return p.read_text().strip()

    def append(self, stream: str, event: Dict[str, Any]) -> AppendResult:
        assert stream in STREAMS
        prev = self.last_hash(stream)
        ts = int(time.time() * 1000)
        payload = {"ts": ts, "prev": prev, "event": event}
        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        h = sha256(raw)
        out = self.data_dir / stream / f"{ts}.{h}.json"
        out.write_bytes(raw)
        self._last_hash_path(stream).write_text(h)
        return AppendResult(path=out, entry_hash=h, prev_hash=prev)
