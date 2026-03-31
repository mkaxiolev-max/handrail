from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI
from pydantic import BaseModel

from src.store import AppendOnlyStore, STREAMS
from src.tier import TierLatch

app = FastAPI(title="Continuum v0")

DATA_DIR = Path.home() / "axiolev" / "continuum" / "data"
STATE_PATH = DATA_DIR / "tier_state.json"
SSD_ALEXANDRIA = Path("/Volumes/NSExternal/ALEXANDRIA")

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

@app.get("/continuum/status")
def continuum_status():
    """Structured health + state for CPS health_check plans."""
    s = latch.get()
    stream_counts: Dict[str, int] = {}
    streams_dir = DATA_DIR / "streams"
    for stream in STREAMS:
        d = streams_dir / stream
        stream_counts[stream] = len(list(d.glob("*.json"))) if d.exists() else 0
    ssd_mounted = SSD_ALEXANDRIA.exists()
    return {
        "ok": True,
        "service": "continuum",
        "version": "v0",
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tier_state": {
            "global_tier": s.global_tier,
            "isolated_domains": s.isolated_domains,
        },
        "streams": stream_counts,
        "ssd_mounted": ssd_mounted,
        "data_dir": str(DATA_DIR),
    }
