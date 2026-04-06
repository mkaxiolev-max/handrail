"""Engine router — /api/v1/engine/*"""
import json
import httpx
from pathlib import Path
from fastapi import APIRouter, HTTPException
from shared.models.engine import IntentExecution, DisputeRecord, ReplayRequest, SimulateRequest
from shared.models.enums import OpDecision
from shared.receipts.verifier import ReceiptVerifier
from ns_api.app.config import ALEXANDRIA_PATH, HANDRAIL_URL

router = APIRouter(prefix="/api/v1/engine", tags=["engine"])

_receipts_dir = ALEXANDRIA_PATH / "receipts"
_ns_memory_path = ALEXANDRIA_PATH / ".run" / "ns_memory.json"


def _load_recent_runs(limit: int = 20) -> list[dict]:
    ledger = _receipts_dir / "receipt_chain.jsonl"
    if ledger.exists():
        lines = ledger.read_text().strip().splitlines()
        return [json.loads(l) for l in lines[-limit:] if l]
    return []


def _last_receipt() -> dict | None:
    files = sorted(
        [f for f in _receipts_dir.glob("*.json") if f.is_file()],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    if files:
        try:
            return json.loads(files[0].read_text())
        except Exception:
            pass
    return None


def _current_intent() -> dict:
    if _ns_memory_path.exists():
        try:
            return json.loads(_ns_memory_path.read_text())
        except Exception:
            pass
    return {}


@router.get("/live")
async def get_live():
    # Probe Handrail status
    handrail_status = None
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.post(
                f"{HANDRAIL_URL}/intent/execute",
                json={"text": "status"},
            )
            if r.status_code == 200:
                handrail_status = r.json()
    except Exception as e:
        handrail_status = {"error": str(e)}

    last_receipt = _last_receipt()
    current_intent = _current_intent()

    return {
        "current_intent": current_intent,
        "last_receipt": last_receipt,
        "handrail_probe": handrail_status,
        "execution_queue": [],
        "adjudication": {
            "scores": [],
            "conflicts": [],
            "selected_path": "live",
            "canon_gate_result": "allow",
        },
    }


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
