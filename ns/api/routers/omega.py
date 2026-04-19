"""Omega L10 Projection/Ego Layer — FastAPI router.

Routes:
  POST /projections         → ProjectionRequest → ProjectionResult
  GET  /projections/{id}    → cached ProjectionResult
  POST /storytime           → {projection_ref, narrative, arc} → Storytime
  GET  /storytime/{id}      → Storytime

Every Storytime emission writes a receipt `narrative_emitted_with_receipt_hash`
to the Lineage Fabric. Canon promotion is NOT exposed here (I1).
AXIOLEV Holdings LLC © 2026
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ns.domain.models.omega_primitives import (
    ProjectionRequest,
    ProjectionResult,
    Storytime,
)
from ns.integrations.omega_store import OmegaStore
from ns.services.omega.projection_engine import ProjectionEngine

router = APIRouter(prefix="/omega", tags=["omega"])

_store = OmegaStore()
_engine = ProjectionEngine(store=_store)


# ------------------------------------------------------------------
# Projections
# ------------------------------------------------------------------


@router.post("/projections", response_model=ProjectionResult)
async def create_projection(req: ProjectionRequest) -> ProjectionResult:
    return _engine.project(req)


@router.get("/projections/{projection_id}", response_model=ProjectionResult)
async def get_projection(projection_id: str) -> ProjectionResult:
    data = _store.read_projection(projection_id)
    if data is None:
        raise HTTPException(status_code=404, detail="projection_not_found")
    return ProjectionResult(**data)


# ------------------------------------------------------------------
# Storytime
# ------------------------------------------------------------------


class StorytimeRequest(BaseModel):
    projection_ref: str
    narrative: str
    arc: list[str] = []


@router.post("/storytime", response_model=Storytime)
async def create_storytime(req: StorytimeRequest) -> Storytime:
    st_id = str(uuid.uuid4())
    st = Storytime(
        id=st_id,
        projection_ref=req.projection_ref,
        narrative=req.narrative,
        arc=req.arc,
    )
    sha = _store.write_storytime(st_id, st.model_dump(mode="json"))
    _store.append_receipt(
        {
            "name": "narrative_emitted_with_receipt_hash",
            "storytime_id": st_id,
            "projection_ref": req.projection_ref,
            "sha256": sha,
        }
    )
    return st


@router.get("/storytime/{st_id}", response_model=Storytime)
async def get_storytime(st_id: str) -> Storytime:
    data = _store.read_storytime(st_id)
    if data is None:
        raise HTTPException(status_code=404, detail="storytime_not_found")
    return Storytime(**data)
