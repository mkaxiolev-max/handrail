# Copyright © 2026 Axiolev. All rights reserved.
"""
Violet ISR Renderer — 4 CPS ops
Assembles an Intelligence Status Report (ISR) from live system state.
Runs inside Handrail container; uses Docker-internal service names.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_NS_MEMORY_FILE = Path("/Volumes/NSExternal/.run/ns_memory.json")
_RECEIPTS_DIR   = Path("/Volumes/NSExternal/receipts")

# Inside Docker: use localhost for self (handrail), container names for peers.
# Adapter runs on Mac host → host.docker.internal.
_SERVICES = {
    "handrail":  "http://127.0.0.1:8011/healthz",
    "ns":        "http://ns:9000/healthz",
    "atomlex":   "http://atomlex:8080/healthz",
    "continuum": "http://continuum:8788/healthz",
    "adapter":   "http://host.docker.internal:8765/healthz",
}


def _ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ---------------------------------------------------------------------------
# Op: violet.render_status
# ---------------------------------------------------------------------------

def _op_violet_render_status(args: dict, _policy) -> dict:
    """GET /healthz on all 5 services → {ok, services, timestamp}.
    Handrail is self-reported as healthy (calling own port deadlocks sync handler).
    """
    services: dict[str, dict] = {}
    all_ok = True
    for name, url in _SERVICES.items():
        if name == "handrail":
            # Self — if this code is running, handrail is up
            services[name] = {"ok": True, "status_code": 200, "note": "self"}
            continue
        try:
            r = httpx.get(url, timeout=5.0)
            ok = r.status_code == 200
            services[name] = {"ok": ok, "status_code": r.status_code}
        except Exception as exc:
            ok = False
            services[name] = {"ok": False, "error": str(exc)}
        if not ok:
            all_ok = False
    return {"ok": all_ok, "services": services, "timestamp": _ts()}


# ---------------------------------------------------------------------------
# Op: violet.render_last_intent
# ---------------------------------------------------------------------------

def _op_violet_render_last_intent(args: dict, _policy) -> dict:
    """Read last entry from ns_memory.json → intent fields."""
    if not _NS_MEMORY_FILE.exists():
        return {"ok": True, "last_intent": None}
    try:
        data = json.loads(_NS_MEMORY_FILE.read_text())
        return {
            "ok": True,
            "intent_text":  data.get("intent_text") or data.get("last_intent"),
            "op_resolved":  data.get("op_resolved") or data.get("last_run_id"),
            "result":       data.get("result") or {"last_ok": data.get("last_ok")},
            "timestamp":    data.get("timestamp") or data.get("ts"),
            "receipt_id":   data.get("receipt_id") or data.get("last_digest"),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "last_intent": None}


# ---------------------------------------------------------------------------
# Op: violet.render_memory_summary
# ---------------------------------------------------------------------------

def _op_violet_render_memory_summary(args: dict, _policy) -> dict:
    """Last 10 receipts from /Volumes/NSExternal/receipts/ by mtime."""
    if not _RECEIPTS_DIR.exists():
        return {"ok": True, "atom_count": 0, "last_10": []}
    try:
        files = sorted(
            (f for f in _RECEIPTS_DIR.iterdir() if f.is_file()),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        atom_count = len(files)
        last_10: list[dict] = []
        for f in files[:10]:
            try:
                d = json.loads(f.read_text())
                last_10.append({
                    "receipt_id": d.get("receipt_id", f.stem),
                    "event_type": d.get("event_type") or d.get("op") or d.get("type") or "unknown",
                    "timestamp":  d.get("timestamp") or d.get("ts") or d.get("ingested_at") or "",
                })
            except Exception:
                last_10.append({"receipt_id": f.stem, "event_type": "unknown", "timestamp": ""})
        return {"ok": True, "atom_count": atom_count, "last_10": last_10}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "atom_count": 0, "last_10": []}


# ---------------------------------------------------------------------------
# Op: violet.isr_full
# ---------------------------------------------------------------------------

def _op_violet_isr_full(args: dict, policy) -> dict:
    """Assemble full ISR: status + last_intent + memory_summary."""
    status         = _op_violet_render_status({}, policy)
    last_intent    = _op_violet_render_last_intent({}, policy)
    memory_summary = _op_violet_render_memory_summary({}, policy)
    return {
        "ok":             True,
        "status":         status,
        "last_intent":    last_intent,
        "memory_summary": memory_summary,
        "shalom":         True,
        "assembled_at":   _ts(),
    }


# ---------------------------------------------------------------------------
# Registry export
# ---------------------------------------------------------------------------

VIOLET_OPS: dict[str, Any] = {
    "violet.render_status":         _op_violet_render_status,
    "violet.render_last_intent":    _op_violet_render_last_intent,
    "violet.render_memory_summary": _op_violet_render_memory_summary,
    "violet.isr_full":              _op_violet_isr_full,
}
