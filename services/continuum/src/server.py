from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI
from pydantic import BaseModel

from src.store import AppendOnlyStore
from src.tier import TierLatch

app = FastAPI(title="Continuum v0")

DATA_DIR = Path.home() / "axiolev" / "continuum" / "data"
STATE_PATH = DATA_DIR / "tier_state.json"

store = AppendOnlyStore(DATA_DIR / "streams")
latch = TierLatch(STATE_PATH)

class AppendIn(BaseModel):
    stream: str
    event: Dict[str, Any]

@app.get("/state")
def get_state():
    s = latch.get()
    return {"global_tier": s.global_tier, "isolated_domains": s.isolated_domains}

@app.post("/append")
def append_event(inp: AppendIn):
    r = store.append(inp.stream, inp.event)
    return {"ok": True, "path": str(r.path), "entry_hash": r.entry_hash, "prev_hash": r.prev_hash}

@app.post("/receipts")
def ingest_receipt(inp: AppendIn):
    r = store.append("operational", {"type": "receipt", **inp.event})
    return {"ok": True, "path": str(r.path), "entry_hash": r.entry_hash, "prev_hash": r.prev_hash}
