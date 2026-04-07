from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/sources", tags=["sources"])

class SourceRegisterIn(BaseModel):
    kind: str
    path: str
    sync_mode: str = "incremental"

@router.post("/register")
async def register_source(payload: SourceRegisterIn):
    return {"status": "registered", "source": payload.dict()}

@router.get("/list")
async def list_sources():
    return {"sources": []}

@router.get("/healthz")
async def health():
    return {"status": "ok"}
