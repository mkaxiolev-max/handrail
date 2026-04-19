"""NS∞ API server — FastAPI application with lifespan.

Routers mounted:
  /canon     — Ring 4 canon promotion gate
  /ril       — RIL engines
  /oracle    — Oracle v2
  /ui        — UI runtime
  /omega     — Omega L10 Projection/Ego Layer (Z3)

AXIOLEV Holdings LLC © 2026
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from ns.api.routers import canon, oracle, ril, ui_runtime
from ns.api.routers import omega as omega_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup: ensure Omega archive layout exists
    from ns.integrations.omega_store import OmegaStore
    OmegaStore()  # triggers _ensure_layout
    yield
    # Shutdown: no-op — append-only stores need no teardown


app = FastAPI(title="NS∞ API", version="1.0.0", lifespan=lifespan)

app.include_router(canon.router)
app.include_router(ril.router)
app.include_router(oracle.router)
app.include_router(ui_runtime.router)
app.include_router(omega_router.router)


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}
