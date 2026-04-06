from typing import Any, Optional
from datetime import datetime
from .base import StrictModel, utc_now


class WSEvent(StrictModel):
    event_type: str
    payload: dict[str, Any] = {}
    timestamp: datetime = None

    def model_post_init(self, __context):
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", utc_now())


class WSBootEvent(WSEvent):
    event_type: str = "boot"


class WSOpEvent(WSEvent):
    event_type: str = "op"
    run_id: Optional[str] = None
    op: Optional[str] = None
    ok: bool = True


class WSProgramEvent(WSEvent):
    event_type: str = "program"
    program_id: Optional[str] = None
    state_change: Optional[str] = None


class WSAlertEvent(WSEvent):
    event_type: str = "alert"
    level: str = "info"
    message: str = ""
