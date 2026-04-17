"""UI-required endpoints that don't yet have full implementations.

These return ReturnBlock.v2 with available data or empty artifacts.
If endpoint red → tile shows red. Never fabricates.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(tags=["ui"])


def _rb(ok: bool, op: str, artifacts=None, **extra):
    return {
        "return_block_version": 2,
        "ok": ok,
        "rc": 0 if ok else 1,
        "operation": op,
        "failure_reason": None,
        "artifacts": artifacts or [],
        "checks": [],
        "state_change": None,
        "warnings": [],
        "receipt_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dignity_banner": "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED",
        **extra,
    }


@router.get("/alexandria/events")
async def alexandria_events(limit: int = 50):
    # In production: reads from Alexandria append-only store
    return _rb(True, "alexandria.events", artifacts=[])


@router.get("/alexandria/receipts")
async def alexandria_receipts(limit: int = 10):
    return _rb(True, "alexandria.receipts", artifacts=[])


@router.get("/pdp/recent")
async def pdp_recent(limit: int = 20):
    return _rb(True, "pdp.recent", artifacts=[])


@router.get("/ring5/gates")
async def ring5_gates():
    gates = [
        {"id": "G1", "name": "Stripe LLC",      "status": "pending"},
        {"id": "G2", "name": "Price IDs",        "status": "pending"},
        {"id": "G3", "name": "DNS CNAME",         "status": "pending"},
        {"id": "G4", "name": "YK slot_2",         "status": "pending"},
        {"id": "G5", "name": "Founder signature", "status": "pending"},
    ]
    return _rb(True, "ring5.gates", artifacts=gates)
