"""CI-2 DisclosureWindow — time-bounded fact visibility."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


class DisclosureWindow:
    def __init__(
        self,
        open_at: Optional[datetime] = None,
        close_at: Optional[datetime] = None,
    ):
        self._open = open_at
        self._close = close_at

    def is_disclosable(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now(timezone.utc)
        if self._open and now < self._open:
            return False
        if self._close and now > self._close:
            return False
        return True

    def evaluate(self, candidate: dict, now: Optional[datetime] = None) -> bool:
        """Returns True (must abstain) when outside disclosure window."""
        return not self.is_disclosable(now)
