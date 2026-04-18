"""PIIC chain — monotonic forward progression through 4 stages (B3).

Stages (in order): perception → interpretation → identification → commitment
No skipping; no rollback (I10 — monotone supersession).
"""
from __future__ import annotations

from enum import Enum


class PIICStage(str, Enum):
    perception = "perception"
    interpretation = "interpretation"
    identification = "identification"
    commitment = "commitment"


STAGE_ORDER: list[PIICStage] = [
    PIICStage.perception,
    PIICStage.interpretation,
    PIICStage.identification,
    PIICStage.commitment,
]


class PIICChain:
    """Monotonic PIIC stage chain.  Advance one step at a time; never regress."""

    def __init__(self) -> None:
        self.stage: PIICStage = PIICStage.perception
        self._history: list[PIICStage] = [PIICStage.perception]

    def advance(self) -> PIICStage:
        """Advance exactly one stage forward."""
        idx = STAGE_ORDER.index(self.stage)
        if idx + 1 >= len(STAGE_ORDER):
            raise ValueError(f"Cannot advance beyond terminal stage {self.stage.value!r}")
        self.stage = STAGE_ORDER[idx + 1]
        self._history.append(self.stage)
        return self.stage

    def advance_to(self, target: PIICStage) -> PIICStage:
        """Advance to a specific next stage (must be exactly one step forward)."""
        current_idx = STAGE_ORDER.index(self.stage)
        target_idx = STAGE_ORDER.index(target)
        if target_idx <= current_idx:
            raise ValueError(
                f"Cannot regress PIIC: {self.stage.value!r} → {target.value!r}"
            )
        if target_idx > current_idx + 1:
            raise ValueError(
                f"Cannot skip PIIC stages: {self.stage.value!r} → {target.value!r}"
            )
        self.stage = target
        self._history.append(self.stage)
        return self.stage

    def is_committed(self) -> bool:
        return self.stage == PIICStage.commitment

    @property
    def history(self) -> list[PIICStage]:
        return list(self._history)
