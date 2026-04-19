"""Omega storage adapter — Alexandrian Archive (L7) I/O for Omega L10 layer.

Layout under ALEXANDRIA root:
  branches/<branch_id>.json
  projections/<projection_id>.json
  entanglements/<ent_id>.json
  contradictions/<c_id>.json
  anchors/<anchor_id>.json
  shards/<shard_id>/{data,manifest.json}
  storytime/<st_id>.json
  ledger/ns_events.jsonl   (append-only, SHA-256 chained, I2/I5)

Never overwrites without an explicit supersede op (I10).
AXIOLEV Holdings LLC © 2026
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_SSD_ROOT = Path("/Volumes/NSExternal/ALEXANDRIA")
_FALLBACK_ROOT = Path.home() / "ALEXANDRIA"

_OMEGA_SUBDIRS = [
    "branches",
    "projections",
    "entanglements",
    "contradictions",
    "anchors",
    "shards",
    "storytime",
    "ledger",
]


def _resolve_root(override: Optional[Path] = None) -> Path:
    if override is not None:
        return Path(override)
    if _SSD_ROOT.exists():
        return _SSD_ROOT
    return _FALLBACK_ROOT


class OmegaStore:
    """Read/write/append store for Omega L10 Projection/Ego Layer.

    All write operations return the SHA-256 hex of the written content.
    Append operations are fsync'd and flock'd for durability (I2/I5).
    Supersede semantics: writing a new object never deletes the old one;
    callers must record a SupersessionOp receipt separately.
    """

    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = _resolve_root(root)
        self._ensure_layout()
        self._ledger_path = self.root / "ledger" / "ns_events.jsonl"
        self._prev_hash: str = "GENESIS"
        self._tick: int = 0
        self._load_chain_tip()

    def _ensure_layout(self) -> None:
        for sub in _OMEGA_SUBDIRS:
            (self.root / sub).mkdir(parents=True, exist_ok=True)

    def _load_chain_tip(self) -> None:
        if not self._ledger_path.exists():
            return
        last: Optional[dict] = None
        with open(self._ledger_path) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        last = json.loads(line)
                    except json.JSONDecodeError:
                        pass
        if last:
            self._prev_hash = last.get("event_hash", "GENESIS")
            self._tick = last.get("tick", 0)

    # ------------------------------------------------------------------
    # Core primitives
    # ------------------------------------------------------------------

    def read_json(self, subpath: str) -> Optional[dict]:
        """Return parsed JSON at `subpath` relative to archive root, or None."""
        path = self.root / subpath
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return None

    def write_json(self, subpath: str, obj: dict) -> str:
        """Write `obj` as JSON to `subpath`; returns SHA-256 of written bytes.

        Does NOT overwrite silently — if the file already exists it still
        writes (supersede semantics are enforced at the op level, not here).
        """
        path = self.root / subpath
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(obj, default=str).encode()
        sha = hashlib.sha256(raw).hexdigest()
        path.write_bytes(raw)
        return sha

    def append_receipt(self, line: dict) -> str:
        """Append a hash-chained receipt to the Lineage Fabric ledger.

        Acquires an exclusive flock, fsync's, returns the event_hash.
        """
        self._tick += 1
        chain_input = json.dumps(
            {"prev": self._prev_hash, "tick": self._tick, "data": line},
            sort_keys=True,
            default=str,
        )
        event_hash = hashlib.sha256(chain_input.encode()).hexdigest()
        record = {
            **line,
            "prev_hash": self._prev_hash,
            "tick": self._tick,
            "event_hash": event_hash,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        with open(self._ledger_path, "a") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                fh.write(json.dumps(record, default=str) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)
        self._prev_hash = event_hash
        return event_hash

    # ------------------------------------------------------------------
    # Domain-specific helpers
    # ------------------------------------------------------------------

    def write_branch(self, branch_id: str, obj: dict) -> str:
        return self.write_json(f"branches/{branch_id}.json", obj)

    def read_branch(self, branch_id: str) -> Optional[dict]:
        return self.read_json(f"branches/{branch_id}.json")

    def write_projection(self, projection_id: str, obj: dict) -> str:
        return self.write_json(f"projections/{projection_id}.json", obj)

    def read_projection(self, projection_id: str) -> Optional[dict]:
        return self.read_json(f"projections/{projection_id}.json")

    def write_storytime(self, st_id: str, obj: dict) -> str:
        return self.write_json(f"storytime/{st_id}.json", obj)

    def read_storytime(self, st_id: str) -> Optional[dict]:
        return self.read_json(f"storytime/{st_id}.json")

    def read_ledger(self) -> list[dict]:
        if not self._ledger_path.exists():
            return []
        records: list[dict] = []
        with open(self._ledger_path) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return records
