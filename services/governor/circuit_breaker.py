from __future__ import annotations
from enum import Enum
from collections import deque
from dataclasses import dataclass, field
from typing import Optional
import time

class BreakerState(str, Enum):
    CLOSED="CLOSED"; OPEN="OPEN"; HALF_OPEN="HALF_OPEN"

@dataclass
class NygardCircuitBreaker:
    state: BreakerState=BreakerState.CLOSED
    block_threshold: int=5; window_size: int=20; cooldown_seconds: float=300.0
    recent_outcomes: deque=field(default_factory=lambda:deque(maxlen=20))
    last_open_ts: Optional[float]=None

    def record(self, zone: str) -> BreakerState:
        is_block=(zone=="BLOCK"); self.recent_outcomes.append(is_block); now=time.time()
        if self.state==BreakerState.OPEN:
            if self.last_open_ts and (now-self.last_open_ts)>self.cooldown_seconds:
                self.state=BreakerState.HALF_OPEN
            return self.state
        if self.state==BreakerState.HALF_OPEN:
            self.state=BreakerState.OPEN if is_block else BreakerState.CLOSED
            if is_block: self.last_open_ts=now
            return self.state
        if sum(1 for x in self.recent_outcomes if x)>=self.block_threshold:
            self.state=BreakerState.OPEN; self.last_open_ts=now
        return self.state

    def force_reset(self):
        self.state=BreakerState.CLOSED; self.last_open_ts=None
