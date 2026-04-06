"""Engine router — /api/v1/engine/*"""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from shared.models.engine import IntentExecution, DisputeRecord, ReplayRequest, SimulateRequest
from shared.models.enums import OpDecision
from shared.receipts.verifier import ReceiptVerifier
from ns_api.app.config import ALEXANDRIA_PATH

router = APIRouter(prefix="/api/v1/engine", tags=["engine"])

_runs_file = ALEXANDRIA_PATH / ".runs" / "ledger_chain.json"
_receipts_dir = ALEXANDRIA_PATH / "receipts"


def _load_recent_runs(limit: int = 20) -> list[dict]:
    # Try Alexandria receipts first
    ledger = _receipts_dir / "receipt_chain.jsonl"
    if ledger.exists():
        lines = ledger.read_text().strip().splitlines()
        return [json.loads(l) for l in lines[-limit:] if l]
    return []


@router.get("/live", response_model=list[dict])
async def get_live():
    return _load_recent_runs(10)


@router.get("/intents/{run_id}")
async def get_intent(run_id: str):
    # Search ledger for run_id
    runs = _load_recent_runs(100)
    for r in runs:
        if r.get("receipt_id") == run_id or r.get("run_id") == run_id:
            return r
    raise HTTPException(status_code=404, detail=f"Intent run {run_id} not found")


@router.get("/disputes", response_model=list[DisputeRecord])
async def get_disputes():
    return []


@router.post("/replay/{receipt_id}")
async def replay(receipt_id: str):
    verifier = ReceiptVerifier(_receipts_dir)
    receipt = verifier.get(receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail=f"Receipt {receipt_id} not found")
    return {"replayed": True, "receipt": receipt.model_dump(mode="json"), "dry_run": True}


@router.post("/simulate")
async def simulate(request: SimulateRequest):
    return {
        "simulated": True,
        "ops_count": len(request.ops),
        "dry_run": request.dry_run,
        "results": [{"op": op.get("op", "unknown"), "ok": True} for op in request.ops],
    }
