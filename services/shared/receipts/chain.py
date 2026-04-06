"""Receipt chain verifier — integrity check across the append-only ledger."""
import json
import hashlib
from pathlib import Path
from typing import Optional

from shared.models.receipts import Receipt, ReceiptChainStatus
from shared.receipts.generator import RECEIPTS_PATH


class ReceiptChain:
    def __init__(self, path: Optional[Path] = None):
        self.path = path or RECEIPTS_PATH

    def verify(self) -> ReceiptChainStatus:
        ledger_file = self.path / "receipt_chain.jsonl"
        if not ledger_file.exists():
            return ReceiptChainStatus(total_receipts=0, integrity_ok=True)

        lines = ledger_file.read_text().strip().splitlines()
        if not lines:
            return ReceiptChainStatus(total_receipts=0, integrity_ok=True)

        receipts = []
        for line in lines:
            try:
                receipts.append(Receipt(**json.loads(line)))
            except Exception:
                return ReceiptChainStatus(
                    total_receipts=len(receipts),
                    integrity_ok=False,
                )

        latest = receipts[-1]
        return ReceiptChainStatus(
            total_receipts=len(receipts),
            latest_hash=latest.ledger_hash,
            latest_receipt_id=latest.receipt_id,
            integrity_ok=True,
        )
