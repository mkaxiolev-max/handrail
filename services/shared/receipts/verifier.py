"""Single-receipt verifier — lookup by receipt_id."""
import json
from pathlib import Path
from typing import Optional

from shared.models.receipts import Receipt
from shared.receipts.generator import RECEIPTS_PATH


class ReceiptVerifier:
    def __init__(self, path: Optional[Path] = None):
        self.path = path or RECEIPTS_PATH

    def get(self, receipt_id: str) -> Optional[Receipt]:
        receipt_file = self.path / f"{receipt_id}.json"
        if not receipt_file.exists():
            return None
        try:
            return Receipt(**json.loads(receipt_file.read_text()))
        except Exception:
            return None
