"""FastAPI router with 9 Aletheia-Control endpoints."""
from __future__ import annotations
from functools import lru_cache
from fastapi import APIRouter, Depends, HTTPException, status
from .models import (ControlInput, ControlClassification, ControlAtom,
                     InfluenceChain, ConcernWasteRoute, AletheiaControlReceipt)
from .classifier import classify
from .service import AletheiaControlService

router = APIRouter(prefix="/aletheia-control", tags=["aletheia-control"])

@lru_cache(maxsize=1)
def get_service() -> AletheiaControlService:
    return AletheiaControlService()

@router.post("/classify", response_model=ControlClassification)
def ep_classify(inp: ControlInput, svc=Depends(get_service)):
    cls = classify(inp); svc.record_classification(inp, cls); return cls

@router.post("/route", response_model=AletheiaControlReceipt)
def ep_route(inp: ControlInput, svc=Depends(get_service)):
    return svc.route(inp)

@router.post("/execute-control", response_model=AletheiaControlReceipt)
def ep_execute(atom: ControlAtom, svc=Depends(get_service)):
    return svc.execute_control(atom)

@router.post("/register-influence", response_model=AletheiaControlReceipt)
def ep_influence(chain: InfluenceChain, svc=Depends(get_service)):
    return svc.register_influence(chain)

@router.post("/delete-concern", response_model=AletheiaControlReceipt)
def ep_delete(route: ConcernWasteRoute, svc=Depends(get_service)):
    return svc.delete_concern(route)

@router.post("/receipt", response_model=AletheiaControlReceipt)
def ep_receipt(rcp: AletheiaControlReceipt, svc=Depends(get_service)):
    return svc.persist_receipt(rcp)

@router.get("/dashboard")
def ep_dashboard(svc=Depends(get_service)):
    return svc.dashboard()

@router.get("/score")
def ep_score(svc=Depends(get_service)):
    return svc.score()

@router.post("/weekly-audit")
def ep_audit(svc=Depends(get_service)):
    return svc.weekly_audit()
