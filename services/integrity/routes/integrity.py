"""
Legacy in-memory stub — routes superseded by receipt_chain.py (postgres-backed).
Kept for router registration compatibility.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/integrity", tags=["integrity"])
