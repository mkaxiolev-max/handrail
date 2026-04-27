"""Six Canonical Receipt Types — hash-chained event attestation."""
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ReceiptType(str, Enum):
    FIRST_PRINCIPLES      = "first_principles"
    DELETION_PROOF        = "deletion_proof"
    SIMPLIFICATION_DELTA  = "simplification_delta"
    ALETHEIA_STATE        = "aletheia_state"
    EXTERNAL_EVENT        = "external_event"
    CERTIFICATION_ARTIFACT = "certification_artifact"


@dataclass
class Receipt:
    receipt_type: str
    payload: dict
    ts: str
    prev_hash: str
    self_hash: str = field(default="", init=False)

    def __post_init__(self) -> None:
        body = json.dumps({"receipt_type": self.receipt_type,
                           "payload": self.payload, "ts": self.ts,
                           "prev_hash": self.prev_hash}, sort_keys=True)
        self.self_hash = "sha256:" + hashlib.sha256(body.encode()).hexdigest()


class ReceiptChain:
    GENESIS = "sha256:GENESIS"

    def __init__(self):
        self._chain: list[Receipt] = []

    def _last_hash(self) -> str:
        return self._chain[-1].self_hash if self._chain else self.GENESIS

    def emit(self, receipt_type: ReceiptType, payload: dict) -> Receipt:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        r = Receipt(receipt_type.value, payload, ts, self._last_hash())
        self._chain.append(r)
        return r

    def verify(self) -> bool:
        prev = self.GENESIS
        for r in self._chain:
            if r.prev_hash != prev:
                return False
            body = json.dumps({"receipt_type": r.receipt_type,
                               "payload": r.payload, "ts": r.ts,
                               "prev_hash": r.prev_hash}, sort_keys=True)
            expected = "sha256:" + hashlib.sha256(body.encode()).hexdigest()
            if r.self_hash != expected:
                return False
            prev = r.self_hash
        return True

    def length(self) -> int:
        return len(self._chain)

    def all_receipts(self) -> list[Receipt]:
        return list(self._chain)
