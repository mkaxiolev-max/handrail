"""Memory router — /api/v1/memory/*"""
import json
from pathlib import Path
from fastapi import APIRouter
from shared.models.receipts import Receipt, ReceiptChainStatus
from shared.receipts.generator import RECEIPTS_PATH
from shared.receipts.chain import ReceiptChain

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


@router.get("/graph")
async def get_memory_graph():
    """Summary view of the receipt chain as a memory graph."""
    chain = ReceiptChain(RECEIPTS_PATH)
    status = chain.verify()
    return {
        "total_receipts": status.total_receipts,
        "latest_hash": status.latest_hash,
        "latest_receipt_id": status.latest_receipt_id,
        "integrity_ok": status.integrity_ok,
        "receipts_path": str(RECEIPTS_PATH),
    }


@router.get("/receipts", response_model=list[dict])
async def list_receipts(limit: int = 50):
    ledger = RECEIPTS_PATH / "receipt_chain.jsonl"
    if not ledger.exists():
        # Fallback to Alexandria ledger
        alt = Path("/Volumes/NSExternal/ALEXANDRIA/ledger/ns_receipt_chain.jsonl")
        if not alt.exists():
            return []
        ledger = alt

    lines = ledger.read_text().strip().splitlines()
    results = []
    for line in reversed(lines[-limit:]):
        try:
            results.append(json.loads(line))
        except Exception:
            continue
    return results
