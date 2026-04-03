"""
handrail-adapter-macos — FastAPI Server
========================================
Port 9911.  Single endpoint: POST /adapter/v1/run

Handrail CPS calls this via http.post op:
  {
    "op": "http.post",
    "args": {
      "url": "http://host.docker.internal:9911/adapter/v1/run",
      "json": { "method": "env.health", "params": {} }
    }
  }

Response shape is always AdapterResponse (see adapter_core.contract).
"""
import logging, os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from adapter_core.contract import AdapterRequest, AdapterResponse
from dignity_kernel import DignityKernel
from macos_driver.handlers import build_registry

# ── Globals ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [ADAPTER] %(message)s")
log = logging.getLogger(__name__)

registry = build_registry()
kernel   = DignityKernel()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("handrail-adapter-macos v1.0 starting on :9911")
    log.info(f"Registered methods: {registry.available_methods()}")
    log.info(f"Mock mode: {os.environ.get('ADAPTER_MOCK', 'auto-detect')}")
    yield
    log.info("Adapter shutdown")


app = FastAPI(title="handrail-adapter-macos", version="1.0.0", lifespan=lifespan)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/healthz")
async def healthz():
    return {
        "ok": True,
        "service": "handrail-adapter-macos",
        "version": "1.0.0",
        "methods": len(registry.available_methods()),
        "dignity_kernel": {
            "violations": kernel.violations,
            "breaker_open": kernel.breaker_open,
        }
    }


# ── Primary execution endpoint ────────────────────────────────────────────────

@app.post("/adapter/v1/run")
async def run_adapter(raw: Request):
    body = await raw.json()
    req  = AdapterRequest(**body)

    log.info(f"→ {req.method} run={req.run_id} action={req.action_id}")

    # Dignity kernel pre-check
    denial = kernel.check(req)
    if denial:
        resp = AdapterResponse.denied(req, denial)
        log.warning(f"✗ DENIED {req.method}: {denial}")
        return JSONResponse(resp.model_dump())

    # Dispatch to handler
    resp = await registry.dispatch(req)

    # Log outcome
    icon = "✓" if resp.status.value == "success" else "✗"
    log.info(f"{icon} {req.method} → {resp.status} [{resp.latency_ms}ms] hash={resp.state_hash}")

    return JSONResponse(resp.model_dump())


# ── Introspection ─────────────────────────────────────────────────────────────

@app.get("/adapter/v1/methods")
async def list_methods():
    return {"methods": registry.available_methods()}

@app.get("/capabilities")
async def capabilities_all():
    from adapter_core.capability_registry import CAPABILITY_REGISTRY, REGISTRY_BY_NAMESPACE
    return {
        "ok": True,
        "total": len(CAPABILITY_REGISTRY),
        "namespaces": sorted(REGISTRY_BY_NAMESPACE.keys()),
        "capabilities": {ns: [e["op"] for e in ops]
                         for ns, ops in REGISTRY_BY_NAMESPACE.items()},
        "full": CAPABILITY_REGISTRY,
    }

@app.get("/capabilities/{namespace}")
async def capabilities_namespace(namespace: str):
    from adapter_core.capability_registry import REGISTRY_BY_NAMESPACE
    ops = REGISTRY_BY_NAMESPACE.get(namespace)
    if ops is None:
        return JSONResponse({"ok": False, "error": f"namespace '{namespace}' not found"}, status_code=404)
    return {"ok": True, "namespace": namespace, "count": len(ops), "ops": ops}


# ── CPS bridge routes — /ops/{namespace}/{action} (port 8765 compat) ─────────
# cps_engine._mac_bridge() calls POST /ops/{ns}/{action} with JSON args body.
# Response must be a flat dict {ok, ...data} for the CPS result layer.

@app.post("/ops/{namespace}/{action}")
async def ops_bridge(namespace: str, action: str, raw: Request):
    method = f"{namespace}.{action}"
    try:
        args = await raw.json()
    except Exception:
        args = {}

    req = AdapterRequest(method=method, params=args if isinstance(args, dict) else {})

    denial = kernel.check(req)
    if denial:
        resp = AdapterResponse.denied(req, denial)
        return JSONResponse({"ok": False, "error": resp.error, "op": method})

    resp = await registry.dispatch(req)
    icon = "✓" if resp.status.value == "success" else "✗"
    log.info(f"{icon} [bridge] {method} → {resp.status} [{resp.latency_ms}ms]")

    if resp.status.value in ("success", "skipped"):
        return {"ok": True, "op": method, **(resp.data or {})}
    return JSONResponse({"ok": False, "op": method, "error": resp.error or resp.status.value}, status_code=200)


@app.get("/ops")
async def list_ops():
    return {"ok": True, "ops": registry.available_methods(), "count": len(registry.available_methods())}


if __name__ == "__main__":
    import uvicorn
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
