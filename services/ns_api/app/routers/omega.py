"""Omega router — /api/v1/omega/*"""

import httpx
from fastapi import APIRouter, HTTPException

from ns_api.app.config import OMEGA_URL

router = APIRouter(prefix="/api/v1/omega", tags=["omega"])


async def _proxy(method: str, path: str, *, json_body: dict | None = None):
    url = f"{OMEGA_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.request(method, url, json=json_body)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text
        raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Omega unavailable: {exc}") from exc


@router.get("/healthz")
async def omega_health():
    return await _proxy("GET", "/healthz")


@router.post("/simulate")
async def omega_simulate(payload: dict):
    return await _proxy("POST", "/omega/simulate", json_body=payload)


@router.get("/runs")
async def omega_runs():
    return await _proxy("GET", "/omega/runs")


@router.get("/runs/{run_id}")
async def omega_run(run_id: str):
    return await _proxy("GET", f"/omega/runs/{run_id}")


@router.get("/runs/{run_id}/branches")
async def omega_run_branches(run_id: str):
    return await _proxy("GET", f"/omega/runs/{run_id}/branches")


@router.post("/runs/{run_id}/compare")
async def omega_compare(run_id: str, payload: dict):
    return await _proxy("POST", f"/omega/runs/{run_id}/compare", json_body=payload)
