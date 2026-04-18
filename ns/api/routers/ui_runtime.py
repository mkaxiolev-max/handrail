"""Founder Console API router — B5 endpoints.

Live-fetch from NCOM/PIIC runtime state for the Founder Console UI.
"""
from __future__ import annotations

import datetime

from fastapi import APIRouter

from ns.api.schemas.ncom_piic import (
    CollapseReadinessSnapshot,
    ContradictionList,
    FounderConsoleHistory,
    FounderConsoleSnapshot,
    HistoryEntry,
    NCOMStateSnapshot,
    ObservationList,
    PIICStageSnapshot,
    ReceiptList,
    RoutingCurrent,
)
from ns.services.ui.engine_room import EngineRoom

router = APIRouter(prefix="/founder-console", tags=["founder-console"])

_engine = EngineRoom()


def _now() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"


@router.get("/snapshot", response_model=FounderConsoleSnapshot)
async def get_snapshot() -> FounderConsoleSnapshot:
    """Current NCOM state + PIIC stage + CollapseReadiness."""
    snap = _engine.snapshot()
    return snap


@router.get("/history", response_model=FounderConsoleHistory)
async def get_history() -> FounderConsoleHistory:
    """Full state/stage transition histories."""
    return _engine.history()


@router.get("/contradictions/active", response_model=ContradictionList)
async def get_active_contradictions() -> ContradictionList:
    """Active contradiction entries from the Gradient Field."""
    return _engine.active_contradictions()


@router.get("/observations/open", response_model=ObservationList)
async def get_open_observations() -> ObservationList:
    """Open observation entries pending PIIC processing."""
    return _engine.open_observations()


@router.get("/routing/current", response_model=RoutingCurrent)
async def get_routing_current() -> RoutingCurrent:
    """Current Loom routing: active layer, top interpretation, route intent."""
    return _engine.routing_current()


@router.get("/receipts/recent", response_model=ReceiptList)
async def get_recent_receipts() -> ReceiptList:
    """Last N receipts from the Lineage Fabric."""
    return _engine.recent_receipts()
