from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

class WatchAction(str, Enum):
    acknowledge = "acknowledge"
    escalate_to_mac = "escalate_to_mac"
    snooze_15m = "snooze_15m"
    request_brief = "request_brief"
    silent = "silent"

@dataclass
class WatchNotification:
    notification_id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    body: str = ""
    action_options: list[WatchAction] = field(default_factory=list)
    urgency: str = "normal"
    created_at: str = field(default_factory=utc_now)
    acknowledged: bool = False

@dataclass
class WatchStateSnapshot:
    snapshot_id: str = field(default_factory=lambda: str(uuid4()))
    ns_status: str = ""
    active_intents: int = 0
    last_receipt: str = ""
    captured_at: str = field(default_factory=utc_now)

class WatchPlane:
    def __init__(self):
        self._notifications: list[WatchNotification] = []
        self._snapshots: list[WatchStateSnapshot] = []

    def notify(self, title: str, body: str, actions: list[WatchAction] | None = None,
               urgency: str = "normal") -> WatchNotification:
        n = WatchNotification(title=title[:25], body=body[:50],
                              action_options=actions or [WatchAction.acknowledge], urgency=urgency)
        self._notifications.append(n)
        return n

    def snapshot(self, ns_status: str, active_intents: int, last_receipt: str) -> WatchStateSnapshot:
        s = WatchStateSnapshot(ns_status=ns_status, active_intents=active_intents,
                               last_receipt=last_receipt[:12])
        self._snapshots.append(s)
        return s

    def pending_notifications(self) -> list[WatchNotification]:
        return [n for n in self._notifications if not n.acknowledged]

    def latest_snapshot(self) -> WatchStateSnapshot | None:
        return self._snapshots[-1] if self._snapshots else None

_watch = WatchPlane()
def get_watch_plane() -> WatchPlane:
    return _watch
