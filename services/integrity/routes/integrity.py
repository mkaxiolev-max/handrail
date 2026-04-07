from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
import datetime
import hashlib

router = APIRouter(prefix="/integrity", tags=["integrity"])

_chain: List[dict] = []

class Receipt(BaseModel):
    op: str
    payload: Optional[dict] = None
    source: Optional[str] = None

@router.post("/receipt")
async def append_receipt(receipt: Receipt):
    prev_hash = _chain[-1]["hash"] if _chain else "0" * 64
    entry = {
        "index": len(_chain),
        "ts": datetime.datetime.utcnow().isoformat(),
        "op": receipt.op,
        "payload": receipt.payload,
        "source": receipt.source,
        "prev_hash": prev_hash,
    }
    entry["hash"] = hashlib.sha256(str(entry).encode()).hexdigest()
    _chain.append(entry)
    return {"status": "appended", "index": entry["index"], "hash": entry["hash"]}

@router.get("/chain")
async def get_chain():
    return {"length": len(_chain), "chain": _chain}

@router.get("/healthz")
async def health():
    return {"status": "ok", "service": "integrity", "chain_length": len(_chain)}
