"""ReceiptGenerator — immutable JSON receipt writer to Alexandria ledger."""
import hashlib
import json
import os
import uuid
from datetime import timezone
from pathlib import Path
from typing import Any, Optional

from shared.models.receipts import Receipt
from shared.models.enums import ReceiptType, RiskTier
from shared.models.base import utc_now


RECEIPTS_PATH = Path(os.environ.get("ALEXANDRIA_PATH", "/Volumes/NSExternal")) / "receipts"


class ReceiptGenerator:
    def __init__(self, receipts_path: Optional[Path] = None):
        self.path = receipts_path or RECEIPTS_PATH
        self.path.mkdir(parents=True, exist_ok=True)
        self._prev_hash: Optional[str] = None

    def _compute_digest(self, payload: dict) -> str:
        canonical = json.dumps(payload, sort_keys=True, default=str)
        return "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()

    def _chain_hash(self, receipt_id: str, digest: str, prev_hash: Optional[str]) -> str:
        chain_input = f"{receipt_id}:{digest}:{prev_hash or 'genesis'}"
        return hashlib.sha256(chain_input.encode()).hexdigest()[:16]

    def issue_receipt(
        self,
        receipt_type: ReceiptType,
        payload: dict[str, Any],
        op: Optional[str] = None,
        actor: str = "system",
        risk_tier: RiskTier = RiskTier.R0,
    ) -> Receipt:
        receipt_id = f"rcpt_{receipt_type.value}_{utc_now().strftime('%Y%m%dT%H%M%S%f')}"
        op_digest = self._compute_digest(payload)
        ledger_hash = self._chain_hash(receipt_id, op_digest, self._prev_hash)

        receipt = Receipt(
            receipt_id=receipt_id,
            receipt_type=receipt_type,
            op=op,
            actor=actor,
            risk_tier=risk_tier,
            payload=payload,
            op_digest=op_digest,
            ledger_hash=ledger_hash,
            prev_hash=self._prev_hash,
        )

        self._prev_hash = ledger_hash
        self._persist(receipt)
        return receipt

    def _persist(self, receipt: Receipt) -> None:
        line = json.dumps(receipt.model_dump(mode="json"), default=str)
        receipt_file = self.path / f"{receipt.receipt_id}.json"
        receipt_file.write_text(line)
        # Also append to chain ledger
        ledger_file = self.path / "receipt_chain.jsonl"
        with ledger_file.open("a") as f:
            f.write(line + "\n")

    def list_receipts(self, limit: int = 50) -> list[Receipt]:
        ledger_file = self.path / "receipt_chain.jsonl"
        if not ledger_file.exists():
            return []
        lines = ledger_file.read_text().strip().splitlines()
        results = []
        for line in reversed(lines[-limit:]):
            try:
                results.append(Receipt(**json.loads(line)))
            except Exception:
                continue
        return results


# Module-level singleton
_generator: Optional[ReceiptGenerator] = None


def get_generator() -> ReceiptGenerator:
    global _generator
    if _generator is None:
        _generator = ReceiptGenerator()
    return _generator
