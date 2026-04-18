"""WebSocket event dispatch for the Founder Console live feed (B6).

Defines the event envelope and a broadcaster that pushes typed events to
connected WebSocket clients.  The actual WS connection management is handled
by the FastAPI app layer; this module owns the event taxonomy only.
"""
from __future__ import annotations

import datetime
import json
from enum import Enum
from typing import Any, Callable, Awaitable


class WSEventType(str, Enum):
    ncom_state_changed = "ncom_state_changed"
    piic_stage_advanced = "piic_stage_advanced"
    readiness_updated = "readiness_updated"
    contradiction_added = "contradiction_added"
    contradiction_cleared = "contradiction_cleared"
    observation_added = "observation_added"
    receipt_appended = "receipt_appended"
    routing_updated = "routing_updated"
    snapshot_refresh = "snapshot_refresh"


class WSEvent:
    def __init__(self, event_type: WSEventType, payload: dict[str, Any]) -> None:
        self.event_type = event_type
        self.payload = payload
        self.timestamp = datetime.datetime.utcnow().isoformat() + "Z"

    def to_json(self) -> str:
        return json.dumps(
            {
                "event": self.event_type.value,
                "payload": self.payload,
                "timestamp": self.timestamp,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "event": self.event_type.value,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


SendFn = Callable[[str], Awaitable[None]]


class FounderConsoleEventBroadcaster:
    """Holds active WebSocket send callbacks and broadcasts typed events.

    Usage in FastAPI WS endpoint:
        broadcaster.register(websocket.send_text)
        try:
            while True:
                await websocket.receive_text()
        finally:
            broadcaster.unregister(websocket.send_text)
    """

    def __init__(self) -> None:
        self._clients: list[SendFn] = []

    def register(self, send_fn: SendFn) -> None:
        if send_fn not in self._clients:
            self._clients.append(send_fn)

    def unregister(self, send_fn: SendFn) -> None:
        self._clients = [c for c in self._clients if c is not send_fn]

    def client_count(self) -> int:
        return len(self._clients)

    async def broadcast(self, event: WSEvent) -> None:
        payload = event.to_json()
        dead: list[SendFn] = []
        for send_fn in list(self._clients):
            try:
                await send_fn(payload)
            except Exception:
                dead.append(send_fn)
        for fn in dead:
            self.unregister(fn)

    async def emit_ncom_state_changed(self, state: str, history: list[str]) -> None:
        await self.broadcast(
            WSEvent(WSEventType.ncom_state_changed, {"state": state, "history": history})
        )

    async def emit_piic_stage_advanced(self, stage: str, history: list[str]) -> None:
        await self.broadcast(
            WSEvent(WSEventType.piic_stage_advanced, {"stage": stage, "history": history})
        )

    async def emit_readiness_updated(self, readiness: dict[str, Any]) -> None:
        await self.broadcast(WSEvent(WSEventType.readiness_updated, readiness))

    async def emit_receipt_appended(self, receipt_name: str, payload: dict[str, Any]) -> None:
        await self.broadcast(
            WSEvent(WSEventType.receipt_appended, {"receipt_name": receipt_name, "payload": payload})
        )

    async def emit_snapshot_refresh(self, snapshot: dict[str, Any]) -> None:
        await self.broadcast(WSEvent(WSEventType.snapshot_refresh, snapshot))


broadcaster = FounderConsoleEventBroadcaster()
