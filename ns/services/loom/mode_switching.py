"""L4 Loom — mode switching for the reflector functor loop.

Loop order: GENERATE → TEST → CONTRADICT → REWEIGHT → NARRATE → STORE → REENTER
"""
from __future__ import annotations

from enum import Enum


class LoomMode(str, Enum):
    GENERATE = "GENERATE"
    TEST = "TEST"
    CONTRADICT = "CONTRADICT"
    REWEIGHT = "REWEIGHT"
    NARRATE = "NARRATE"
    STORE = "STORE"
    REENTER = "REENTER"


_STAGE_ORDER: tuple[LoomMode, ...] = (
    LoomMode.GENERATE,
    LoomMode.TEST,
    LoomMode.CONTRADICT,
    LoomMode.REWEIGHT,
    LoomMode.NARRATE,
    LoomMode.STORE,
    LoomMode.REENTER,
)


class ModeSwitcher:
    """Tracks current loop stage and advances monotonically per cycle."""

    def __init__(self) -> None:
        self._current: LoomMode = LoomMode.GENERATE

    @property
    def current(self) -> LoomMode:
        return self._current

    def advance(self) -> LoomMode:
        """Advance to next stage; stays at REENTER if already terminal."""
        idx = _STAGE_ORDER.index(self._current)
        if idx < len(_STAGE_ORDER) - 1:
            self._current = _STAGE_ORDER[idx + 1]
        return self._current

    def reset(self) -> None:
        self._current = LoomMode.GENERATE

    @staticmethod
    def stage_order() -> tuple[LoomMode, ...]:
        return _STAGE_ORDER
