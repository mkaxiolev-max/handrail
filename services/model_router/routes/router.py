from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import httpx

router = APIRouter(prefix="/router", tags=["router"])

OLLAMA_URL = "http://host.docker.internal:11434"

TASK_ROUTING = {
    "parse_claims": "llama3",
    "extract":      "llama3",
    "classify":     "llama3",
    "summarize":    "mistral",
}
DEFAULT_MODEL = "gpt-oss:20b"


class RunRequest(BaseModel):
    task: str
    prompt: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = {}


def _select_model(task: str) -> str:
    return TASK_ROUTING.get(task, DEFAULT_MODEL)


@router.get("/models")
async def list_models():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            models = [m["name"] for m in data.get("models", [])]
            return {"models": models, "count": len(models), "source": "ollama"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ollama unreachable: {e}")


@router.post("/run")
async def run_route(req: RunRequest):
    selected = _select_model(req.task)
    return {
        "status": "routed",
        "task": req.task,
        "selected_model": selected,
        "ollama_base": OLLAMA_URL,
        "reason": TASK_ROUTING.get(req.task, "default fallback"),
    }


@router.post("/score")
async def score_route(req: RunRequest):
    selected = _select_model(req.task)
    return {
        "task": req.task,
        "selected": selected,
        "fallback": DEFAULT_MODEL if selected != DEFAULT_MODEL else None,
        "reason": "task-routing table" if req.task in TASK_ROUTING else "default",
    }


@router.get("/status")
async def router_status():
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            tags = resp.json()
            local_count = len(tags.get("models", []))
            ollama_ok = True
    except Exception:
        local_count = 0
        ollama_ok = False

    return {
        "ollama_reachable": ollama_ok,
        "local_models_available": local_count,
        "policy": "local-first",
        "routing_table": TASK_ROUTING,
        "default_model": DEFAULT_MODEL,
    }


@router.get("/healthz")
async def health():
    return {"status": "ok"}
