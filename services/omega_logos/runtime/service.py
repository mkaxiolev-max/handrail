"""Ω-Logos HTTP service — AXIOLEV Holdings LLC © 2026.
FastAPI. Exposes the runtime at :9010 with the surface the evaluation pack requires."""
from __future__ import annotations
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from .core import Orchestrator
from .autonomy import Tier, gate, DEFAULT_CEILING
from .failures import COUNTER, Class as F

app = FastAPI(title="Omega-Logos Runtime", version="1.0.0")
orch = Orchestrator(tier=DEFAULT_CEILING)

class StartReq(BaseModel):
    intent: str
    tier: Optional[int] = None
    context: Dict[str, Any] = {}

class StepReq(BaseModel):
    run_id: str
    stage: str
    payload: Dict[str, Any] = {}

class EndReq(BaseModel):
    run_id: str
    result: Dict[str, Any] = {}

class SimulateReq(BaseModel):
    prompt: str
    allow_promotion: bool = False

@app.get("/api/v1/omega/healthz")
def healthz(): return {"ok": True, "service": "omega_logos", "version": "1.0.0"}

@app.post("/api/v1/omega/begin")
def begin(r: StartReq):
    tier = gate(Tier(r.tier) if r.tier is not None else DEFAULT_CEILING)
    st = orch.begin(r.intent, tier=tier)
    return orch.to_dict(st)

@app.post("/api/v1/omega/step")
def step(r: StepReq):
    st = orch.runs.get(r.run_id)
    if not st: raise HTTPException(404, "unknown run_id")
    rec = orch.step(st, r.stage, r.payload)
    return {"receipt": rec.__dict__}

@app.post("/api/v1/omega/end")
def end(r: EndReq):
    st = orch.runs.get(r.run_id)
    if not st: raise HTTPException(404, "unknown run_id")
    rec = orch.end(st, r.result)
    return {"receipt": rec.__dict__, "total_receipts": len(st.receipts)}

@app.get("/api/v1/omega/runs")
def runs():
    return {"runs": [orch.to_dict(s) for s in orch.runs.values()]}

@app.post("/api/v1/omega/simulate")
def simulate(r: SimulateReq):
    # Enforce: canon promotion requires explicit human authority; reject here by default.
    if r.allow_promotion:
        COUNTER.record(F.POLICY_VIOLATION)
        raise HTTPException(403, {"decision": "DIGNITY_KERNEL_VIOLATION",
                                  "reason": "unauthorized canon promotion attempt"})
    return {"decision": "ALLOW", "simulated": r.prompt, "promotion_blocked": True}

@app.get("/api/v1/omega/failures")
def failures():
    return {"distribution": COUNTER.distribution()}
