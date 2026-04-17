"""GET /isr/ner — NER observable endpoint."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter

from isr.ner import compute_ner

router = APIRouter(tags=["isr"])

_RECENT_RECEIPTS: list = []  # populated by Alexandria ingest in production


@router.get("/isr/ner")
async def isr_ner(window: int = 15):
    obs = compute_ner(_RECENT_RECEIPTS, window_minutes=window)
    return {
        "return_block_version": 2,
        "ok": True,
        "rc": 0,
        "operation": "isr.ner",
        "failure_reason": None,
        "artifacts": [obs.model_dump()],
        "checks": [],
        "state_change": None,
        "warnings": [],
        "receipt_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dignity_banner": "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED",
    }
