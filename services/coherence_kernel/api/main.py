"""Coherence Kernel FastAPI stub — Phase 0."""
from __future__ import annotations
from fastapi import FastAPI
from pydantic import BaseModel
from services.coherence_kernel import schemas
from services.coherence_kernel.storage import ledger

app = FastAPI(title="Coherence Kernel", version="0.1.0")


@app.get("/healthz")
def health():
    return {"status": "ok", "service": "coherence_kernel"}


class BranchStateIn(BaseModel):
    branch: schemas.BranchState


@app.post("/branch/register")
def register_branch(body: BranchStateIn):
    rh = ledger.append_branch_state(body.branch.model_dump(mode="json"), body.branch.id)
    return {"row_hash": rh, "branch_id": body.branch.id}


@app.get("/chain/verify/{table}")
def verify_chain(table: str):
    ok = ledger.verify_chain(table)
    return {"table": table, "chain_valid": ok}
