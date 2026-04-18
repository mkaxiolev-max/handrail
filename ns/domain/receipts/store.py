"""Hash-chain reader — verifies I5 provenance inertness."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _hash_entry(name: str, payload: dict, prev_id: str, tick: int) -> str:
    raw = json.dumps(
        {"name": name, "payload": payload, "prev_id": prev_id, "tick": tick},
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode()).hexdigest()


class ChainIntegrityError(Exception):
    """Raised when the hash chain is broken (I5 violation)."""


class ReceiptStore:
    """Read and verify the append-only JSONL hash chain."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    def read_all(self) -> list[dict]:
        if not self._path.exists():
            return []
        records: list[dict] = []
        with open(self._path) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records

    def verify_chain(self) -> bool:
        """Verify hash-chain integrity; raises ChainIntegrityError on violation."""
        prev_id = "GENESIS"
        for rec in self.read_all():
            expected = _hash_entry(
                rec["name"], rec["payload"], rec["prev_id"], rec["tick"]
            )
            if rec["receipt_id"] != expected:
                raise ChainIntegrityError(
                    f"Hash mismatch at tick {rec['tick']}: "
                    f"expected {expected!r}, got {rec['receipt_id']!r}"
                )
            if rec["prev_id"] != prev_id:
                raise ChainIntegrityError(
                    f"Chain break at tick {rec['tick']}: "
                    f"expected prev_id {prev_id!r}, got {rec['prev_id']!r}"
                )
            prev_id = rec["receipt_id"]
        return True
