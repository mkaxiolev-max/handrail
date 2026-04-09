from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

class DeviceSurface(str, Enum):
    mac_studio = "mac_studio"
    iphone = "iphone"
    apple_watch = "apple_watch"
    ipad = "ipad"
    unknown = "unknown"

@dataclass
class DevicePacket:
    packet_id: str = field(default_factory=lambda: str(uuid4()))
    target_surface: DeviceSurface = DeviceSurface.mac_studio
    event_type: str = ""
    summary: str = ""
    detail: dict[str, Any] = field(default_factory=dict)
    urgency: str = "normal"
    requires_interaction: bool = False
    created_at: str = field(default_factory=utc_now)

class DeviceRouter:
    def __init__(self):
        self._packets: dict[DeviceSurface, list[DevicePacket]] = {s: [] for s in DeviceSurface}

    def route(self, packet: DevicePacket) -> bool:
        self._packets[packet.target_surface].append(packet)
        return True

    def broadcast(self, event_type: str, summary: str, urgency: str = "normal") -> list[DevicePacket]:
        packets = []
        for surface in [DeviceSurface.mac_studio, DeviceSurface.iphone, DeviceSurface.apple_watch]:
            p = DevicePacket(target_surface=surface, event_type=event_type,
                summary=summary[:50] if surface == DeviceSurface.apple_watch else summary,
                detail={} if surface == DeviceSurface.apple_watch else {"event_type": event_type},
                urgency=urgency)
            self.route(p)
            packets.append(p)
        return packets

    def get_pending(self, surface: DeviceSurface) -> list[DevicePacket]:
        return list(self._packets.get(surface, []))

    def boot_sequence_publish(self, system_state: dict) -> dict:
        counts = {}
        for surface in DeviceSurface:
            if surface == DeviceSurface.unknown:
                continue
            summary = f"NS∞ online | {system_state.get('status', 'unknown')}"
            p = DevicePacket(target_surface=surface, event_type="system_boot",
                summary=summary, detail={"endpoints": system_state.get("endpoints", 0)})
            self.route(p)
            counts[surface.value] = 1
        return counts

_router = DeviceRouter()
def get_device_router() -> DeviceRouter:
    return _router
