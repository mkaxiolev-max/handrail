# Copyright © 2026 Axiolev. All rights reserved.
from __future__ import annotations

import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from src.store import AppendOnlyStore, STREAMS
from src.tier import TierLatch

app = FastAPI(title="Continuum v1")

SSD_ALEXANDRIA = Path("/Volumes/NSExternal/ALEXANDRIA")
# Prefer SSD mount for persistence; fall back to container-local
_ssd_continuum = SSD_ALEXANDRIA / "continuum"
DATA_DIR = _ssd_continuum if SSD_ALEXANDRIA.exists() else (Path.home() / "axiolev" / "continuum" / "data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
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

class TierIn(BaseModel):
    tier: int

class IsolateIn(BaseModel):
    domain_id: str

@app.post("/tier/set")
def set_tier(inp: TierIn):
    """Ratchet global tier up (0→2→3). Never decrements."""
    s = latch.set_global_tier(inp.tier)
    return {"ok": True, "global_tier": s.global_tier, "isolated_domains": s.isolated_domains}

@app.post("/tier/isolate")
def isolate_domain(inp: IsolateIn):
    """Isolate a domain — sets global_tier ≥ 2."""
    s = latch.isolate_domain(inp.domain_id)
    return {"ok": True, "global_tier": s.global_tier, "isolated_domains": s.isolated_domains}

@app.get("/healthz")
def healthz():
    """Liveness probe."""
    s = latch.get()
    return {
        "healthy": True,
        "service": "continuum",
        "version": "v1",
        "global_tier": s.global_tier,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


class SessionIn(BaseModel):
    source: str
    event: str
    data: Optional[Dict[str, Any]] = {}


_SESSION_LOG: list[dict] = []   # in-memory ring; SSD is authoritative


@app.get("/sessions")
def list_sessions(n: int = 20):
    """List recent session events from Alexandria + in-memory ring."""
    sessions_dir = SSD_ALEXANDRIA / "sessions" if SSD_ALEXANDRIA.exists() else None
    entries: list[dict] = []
    if sessions_dir and sessions_dir.exists():
        for f in sorted(sessions_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]:
            for line in f.read_text().splitlines()[-4:]:
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass
    entries.extend(_SESSION_LOG[-n:])
    entries.sort(key=lambda x: x.get("ts", ""), reverse=True)
    return {"sessions": entries[:n], "count": len(entries[:n])}


@app.post("/sessions")
def record_session(inp: SessionIn):
    """Record a new session event to SSD + in-memory ring."""
    ts = datetime.now(timezone.utc).isoformat()
    entry = {"ts": ts, "source": inp.source, "event": inp.event, "data": inp.data or {}}
    _SESSION_LOG.append(entry)
    if len(_SESSION_LOG) > 500:
        _SESSION_LOG.pop(0)
    sessions_dir = (SSD_ALEXANDRIA / "sessions" if SSD_ALEXANDRIA.exists()
                    else Path.home() / "ALEXANDRIA" / "sessions")
    sessions_dir.mkdir(parents=True, exist_ok=True)
    with (sessions_dir / f"continuum_{inp.source}.jsonl").open("a") as f:
        f.write(json.dumps(entry) + "\n")
    return {"ok": True, "ts": ts, "source": inp.source, "event": inp.event}


@app.get("/state/current")
def state_current():
    """Aggregated state snapshot — last 10 Alexandria sessions + last receipt."""
    s = latch.get()
    sessions_dir = SSD_ALEXANDRIA / "sessions" if SSD_ALEXANDRIA.exists() else None
    recent: list[dict] = []
    if sessions_dir and sessions_dir.exists():
        for f in sorted(sessions_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:3]:
            for line in f.read_text().splitlines()[-4:]:
                try:
                    recent.append(json.loads(line))
                except Exception:
                    pass
    recent.sort(key=lambda x: x.get("ts", ""), reverse=True)
    return {
        "ok": True,
        "ts": datetime.now(timezone.utc).isoformat(),
        "global_tier": s.global_tier,
        "isolated_domains": s.isolated_domains,
        "recent_sessions": recent[:10],
        "ssd_mounted": SSD_ALEXANDRIA.exists(),
    }


@app.post("/state/sync")
def state_sync():
    """Trigger sync — write a snapshot to Alexandria/snapshots/."""
    s = latch.get()
    snapshot_dir = (SSD_ALEXANDRIA / "snapshots" if SSD_ALEXANDRIA.exists()
                    else Path.home() / "ALEXANDRIA" / "snapshots")
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    ts_tag = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snap = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "source": "continuum_sync",
        "global_tier": s.global_tier,
        "isolated_domains": s.isolated_domains,
        "session_count": len(_SESSION_LOG),
        "ssd_mounted": SSD_ALEXANDRIA.exists(),
    }
    snap_path = snapshot_dir / f"continuum_sync_{ts_tag}.json"
    snap_path.write_text(json.dumps(snap, indent=2))
    return {"ok": True, "snapshot_path": str(snap_path), "ts": snap["ts"]}


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
