from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio

router = APIRouter(prefix="/router", tags=["router"])

model_registry = {
    "local_fast_parser": {
        "provider": "ollama",
        "locality": "local",
        "model": "llama3",
        "cost_class": "free_local",
        "latency_class": "fast"
    },
    "local_mid_synthesizer": {
        "provider": "ollama",
        "locality": "local",
        "model": "mistral",
        "cost_class": "free_local",
        "latency_class": "medium"
    },
    "cloud_reasoner": {
        "provider": "openai",
        "locality": "cloud",
        "cost_class": "high",
        "latency_class": "medium"
    }
}

class RouteScoreRequest(BaseModel):
    task_kind: str
    constraints: Optional[Dict[str, Any]] = {}

@router.post("/score")
async def score_route(req: RouteScoreRequest):
    prefer_local = req.constraints.get("prefer_local", True) if req.constraints else True
    if prefer_local and req.task_kind in ["parse_claims", "extract", "classify", "ui_observation"]:
        return {
            "task_kind": req.task_kind,
            "selected": "local_fast_parser",
            "fallback": "cloud_reasoner",
            "reason": "local-first policy"
        }
    return {
        "task_kind": req.task_kind,
        "selected": "cloud_reasoner",
        "fallback": None,
        "reason": "cloud required"
    }

@router.post("/run")
async def run_route(req: RouteScoreRequest):
    score_result = await score_route(req)
    return {
        "status": "queued",
        "task_kind": req.task_kind,
        "selected_model": score_result["selected"],
        "run_id": "pending"
    }

@router.get("/status")
async def router_status():
    return {
        "local_models_available": 2,
        "cloud_fallback": "enabled",
        "policy": "local-first"
    }

@router.get("/healthz")
async def health():
    return {"status": "ok"}
