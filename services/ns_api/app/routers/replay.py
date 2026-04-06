"""Replay router — /api/v1/replay/*"""
from pathlib import Path
from fastapi import APIRouter, HTTPException
from shared.receipts.verifier import ReceiptVerifier
from shared.receipts.generator import RECEIPTS_PATH

router = APIRouter(prefix="/api/v1/replay", tags=["replay"])

# Also check Alexandria proof path
PROOF_PATHS = [
    RECEIPTS_PATH,
    Path("/Volumes/NSExternal/ALEXANDRIA/ledger"),
    Path("/Volumes/NSExternal/ALEXANDRIA/receipts"),
]


@router.post("/{receipt_id}")
async def replay_receipt(receipt_id: str):
    for path in PROOF_PATHS:
        verifier = ReceiptVerifier(path)
        receipt = verifier.get(receipt_id)
        if receipt:
            return {
                "replayed": True,
                "receipt_id": receipt_id,
                "receipt": receipt.model_dump(mode="json"),
                "source_path": str(path),
                "dry_run": True,
            }
    raise HTTPException(status_code=404, detail=f"Receipt {receipt_id} not found in any Alexandria path")
