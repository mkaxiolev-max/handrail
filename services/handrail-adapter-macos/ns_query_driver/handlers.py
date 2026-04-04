"""
ns_query.* namespace
====================
Shortcut ops for common NS∞ query patterns — wraps internal NS HTTP calls
so CPS plans can invoke them without knowing NS internals.

Ops:
  ns_query.health_full  — comprehensive health across all NS subsystems
  ns_query.context      — current session context snapshot
  ns_query.last_error   — most recent error from NS logs
"""
from __future__ import annotations
import asyncio, platform, time
from adapter_core.contract import AdapterRequest, AdapterResponse, OperationStatus

try:
    import httpx as _httpx
    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False

_NS_URL = "http://localhost:9000"


async def ns_query_health_full(req: AdapterRequest) -> AdapterResponse:
    if not _HAS_HTTPX:
        return AdapterResponse.success(req, {"ok": True, "reason": "httpx_unavailable"})
    try:
        import httpx
        results = {}
        endpoints = [
            ("healthz", "/healthz"),
            ("voice", "/voice/health"),
            ("intel", "/intel/proactive"),
            ("capability", "/capability/graph"),
            ("hic", "/hic/status"),
        ]
        for name, path in endpoints:
            try:
                r = httpx.get(f"{_NS_URL}{path}", timeout=3)
                results[name] = {"status": r.status_code, "ok": r.status_code == 200}
            except Exception as e:
                results[name] = {"status": 0, "ok": False, "error": str(e)[:60]}
        all_ok = all(v["ok"] for v in results.values())
        return AdapterResponse.success(req, {"ok": all_ok, "subsystems": results,
                                              "ts": int(time.time())})
    except Exception as e:
        return AdapterResponse.success(req, {"ok": False, "error": str(e)[:120]})


async def ns_query_context(req: AdapterRequest) -> AdapterResponse:
    if not _HAS_HTTPX:
        return AdapterResponse.success(req, {"ok": True, "reason": "httpx_unavailable"})
    try:
        import httpx
        ctx = {}
        for key, path in [("memory", "/memory/recent?n=3"),
                           ("intel", "/intel/proactive"),
                           ("capability", "/capability/unresolved")]:
            try:
                r = httpx.get(f"{_NS_URL}{path}", timeout=3)
                ctx[key] = r.json() if r.status_code == 200 else {}
            except Exception:
                ctx[key] = {}
        return AdapterResponse.success(req, {"ok": True, "context": ctx, "ts": int(time.time())})
    except Exception as e:
        return AdapterResponse.success(req, {"ok": False, "error": str(e)[:120]})


async def ns_query_last_error(req: AdapterRequest) -> AdapterResponse:
    from pathlib import Path
    ledger = Path("/Volumes/NSExternal/.run/ledger_chain.json")
    if not ledger.exists():
        ledger = Path("/Users/axiolevns/axiolev_runtime/.runs/ledger_chain.json")
    if not ledger.exists():
        return AdapterResponse.success(req, {"ok": True, "last_error": None,
                                              "reason": "no_ledger_found"})
    try:
        import json
        entries = json.loads(ledger.read_text())
        if isinstance(entries, list):
            errors = [e for e in entries if e.get("type") == "error" or not e.get("ok", True)]
            last = errors[-1] if errors else None
        else:
            last = None
        return AdapterResponse.success(req, {"ok": True, "last_error": last,
                                              "total_entries": len(entries) if isinstance(entries, list) else 0})
    except Exception as e:
        return AdapterResponse.success(req, {"ok": True, "error": str(e)[:120]})


def build_ns_query_handlers() -> dict:
    return {
        "ns_query.health_full": ns_query_health_full,
        "ns_query.context":     ns_query_context,
        "ns_query.last_error":  ns_query_last_error,
    }
