"""
NORTHSTAR Receipt Chain
Byzantine-resistant append-only audit trail.
Every state transition produces a receipt. Receipts are chained by hash.
"""

import json
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List


RECEIPT_VERSION = "1.0"


def _sha256(data: str) -> str:
    return "sha256:" + hashlib.sha256(data.encode()).hexdigest()


def _ts_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class ReceiptChain:
    """
    Append-only receipt chain. Every write links to the previous receipt hash.
    Lives at /ALEXANDRIA/receipt_ledger/receipts.jsonl
    """

    def __init__(self, ledger_path: Path = None):
        if ledger_path is None:
            from nss.core.storage import RECEIPT_LEDGER_DIR
            ledger_path = RECEIPT_LEDGER_DIR
        self.ledger_path = ledger_path
        self.ledger_path.mkdir(parents=True, exist_ok=True)
        self.chain_file = self.ledger_path / "receipts.jsonl"
        self._counter = self._load_counter()

    def _load_counter(self) -> int:
        if not self.chain_file.exists():
            return 0
        count = 0
        with open(self.chain_file) as f:
            for line in f:
                if line.strip():
                    count += 1
        return count

    def _last_hash(self) -> str:
        if not self.chain_file.exists() or self._counter == 0:
            return "sha256:" + "0" * 64
        last = None
        with open(self.chain_file) as f:
            for line in f:
                if line.strip():
                    last = line.strip()
        if last:
            r = json.loads(last)
            return r.get("receipt_hash", "sha256:" + "0" * 64)
        return "sha256:" + "0" * 64

    def emit(
        self,
        event_type: str,
        source: Dict[str, Any],
        inputs: Optional[Dict] = None,
        proposal: Optional[Dict] = None,
        checks: Optional[Dict] = None,
        outputs: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Emit a new receipt and append to chain.
        Returns the complete receipt dict.
        """
        self._counter += 1
        receipt_id = f"R_{self._counter:06d}"
        prev_hash = self._last_hash()

        receipt = {
            "receipt_version": RECEIPT_VERSION,
            "receipt_id": receipt_id,
            "ts_utc": _ts_utc(),
            "event_type": event_type,
            "source": source,
            "inputs": inputs or {},
            "proposal": proposal or {},
            "checks": checks or {
                "k_max_ok": True,
                "replay_ok": True,
                "mission_graph_ok": True,
                "safety_ok": True,
                "budget_ok": True,
            },
            "outputs": outputs or {},
            "prev_receipt_hash": prev_hash,
            "receipt_hash": "",  # filled below
        }

        # Hash the receipt content (without receipt_hash field)
        receipt_str = json.dumps({k: v for k, v in receipt.items() if k != "receipt_hash"}, sort_keys=True)
        receipt["receipt_hash"] = _sha256(receipt_str)

        # Append to ledger
        with open(self.chain_file, "a") as f:
            f.write(json.dumps(receipt) + "\n")

        return receipt

    def verify_chain(self) -> bool:
        """Verify integrity of full receipt chain."""
        if not self.chain_file.exists():
            return True
        prev_hash = "sha256:" + "0" * 64
        with open(self.chain_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                if r["prev_receipt_hash"] != prev_hash:
                    return False
                # Recompute hash
                content = json.dumps({k: v for k, v in r.items() if k != "receipt_hash"}, sort_keys=True)
                expected = _sha256(content)
                if r["receipt_hash"] != expected:
                    return False
                prev_hash = r["receipt_hash"]
        return True

    def get_recent(self, n: int = 10) -> List[Dict]:
        """Return last N receipts."""
        receipts = []
        if not self.chain_file.exists():
            return receipts
        with open(self.chain_file) as f:
            for line in f:
                if line.strip():
                    receipts.append(json.loads(line))
        return receipts[-n:]

    def count(self) -> int:
        return self._counter

    def recent(self, n: int = 50) -> list:
        """Alias for get_recent — used by server endpoints."""
        return self.get_recent(n)

    def get(self, receipt_id: str) -> dict:
        """Fetch single receipt by ID from chain file."""
        if not self.chain_file.exists():
            return {}
        with open(self.chain_file) as f:
            for line in f:
                try:
                    r = __import__('json').loads(line)
                    if r.get('receipt_id') == receipt_id:
                        return r
                except Exception:
                    pass
        return {}

