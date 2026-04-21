"""HTTP facade for witness cosigning. AXIOLEV Holdings LLC (c) 2026."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from . import STH, cosign_triad, verify_cosigned, consistency_ok, sth_hash

router = APIRouter(prefix="/witness", tags=["witness"])

class STHIn(BaseModel):
    tree_size: int
    root_hash: str
    timestamp: int
    prev_root_hash: Optional[str] = None

@router.post("/cosign")
def witness_cosign(body: STHIn):
    sth = STH(**body.dict())
    cs = cosign_triad(sth, quorum=2)
    if not cs.valid():
        raise HTTPException(503, "witness quorum not reached")
    if not verify_cosigned(cs):
        raise HTTPException(500, "cosignature self-verification failed")
    return {
        "sth_hash": sth_hash(sth),
        "quorum": cs.quorum,
        "cosignatures": [{"witness_id": c.witness_id, "signature": c.signature} for c in cs.cosignatures],
    }

class ConsistencyIn(BaseModel):
    prev: STHIn
    curr: STHIn

@router.post("/consistency")
def witness_consistency(body: ConsistencyIn):
    prev, curr = STH(**body.prev.dict()), STH(**body.curr.dict())
    return {"ok": consistency_ok(prev, curr)}

@router.get("/healthz")
def healthz():
    return {"status": "ok", "service": "witness", "version": "1.0.0"}
