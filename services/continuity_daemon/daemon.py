"""Continuity Daemon — detects state breaks and enforces continuity invariants."""
from __future__ import annotations
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class StateCheckpoint:
    checkpoint_id: str
    state_hash: str
    ts: str
    metadata: dict


class ContinuityDaemon:
    def __init__(self):
        self._history: list[StateCheckpoint] = []

    @staticmethod
    def _hash(state: Any) -> str:
        return hashlib.sha256(str(state).encode()).hexdigest()[:16]

    def create_checkpoint(self, state: Any, metadata: dict | None = None) -> StateCheckpoint:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        h = self._hash(state)
        cid = f"cp_{len(self._history):04d}_{h}"
        cp = StateCheckpoint(cid, h, ts, metadata or {})
        self._history.append(cp)
        return cp

    def verify_continuity(self, checkpoint: StateCheckpoint, current_state: Any) -> bool:
        return checkpoint.state_hash == self._hash(current_state)

    def detect_break(self, checkpoint: StateCheckpoint, current_state: Any) -> bool:
        return not self.verify_continuity(checkpoint, current_state)

    def checkpoint_history(self) -> list[StateCheckpoint]:
        return list(self._history)

    def last_checkpoint(self) -> StateCheckpoint | None:
        return self._history[-1] if self._history else None

    def history_length(self) -> int:
        return len(self._history)
