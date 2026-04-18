"""NCOM 8-state machine (B2).

States: inactive → priming → observing → branching → stabilizing →
        ready_for_collapse → forced_collapse | aborted
"""
from __future__ import annotations

from enum import Enum


class NCOMState(str, Enum):
    inactive = "inactive"
    priming = "priming"
    observing = "observing"
    branching = "branching"
    stabilizing = "stabilizing"
    ready_for_collapse = "ready_for_collapse"
    forced_collapse = "forced_collapse"
    aborted = "aborted"


VALID_TRANSITIONS: dict[NCOMState, frozenset[NCOMState]] = {
    NCOMState.inactive: frozenset({NCOMState.priming, NCOMState.aborted}),
    NCOMState.priming: frozenset({NCOMState.observing, NCOMState.aborted}),
    NCOMState.observing: frozenset({NCOMState.branching, NCOMState.aborted}),
    NCOMState.branching: frozenset({NCOMState.stabilizing, NCOMState.aborted}),
    NCOMState.stabilizing: frozenset({NCOMState.ready_for_collapse, NCOMState.aborted}),
    NCOMState.ready_for_collapse: frozenset({NCOMState.forced_collapse, NCOMState.aborted}),
    NCOMState.forced_collapse: frozenset(),
    NCOMState.aborted: frozenset(),
}

TERMINAL_STATES: frozenset[NCOMState] = frozenset({NCOMState.forced_collapse, NCOMState.aborted})
COLLAPSE_READY_STATES: frozenset[NCOMState] = frozenset(
    {NCOMState.ready_for_collapse, NCOMState.forced_collapse}
)


class NCOMStateMachine:
    """Deterministic 8-state NCOM machine.  Ratchet-forward; no rollback."""

    def __init__(self) -> None:
        self.state: NCOMState = NCOMState.inactive
        self._history: list[NCOMState] = [NCOMState.inactive]

    def transition(self, target: NCOMState) -> NCOMState:
        allowed = VALID_TRANSITIONS.get(self.state, frozenset())
        if target not in allowed:
            raise ValueError(
                f"Invalid NCOM transition: {self.state.value!r} → {target.value!r}. "
                f"Allowed: {[s.value for s in allowed]}"
            )
        self.state = target
        self._history.append(target)
        return self.state

    def is_terminal(self) -> bool:
        return self.state in TERMINAL_STATES

    def is_collapse_ready(self) -> bool:
        return self.state in COLLAPSE_READY_STATES

    @property
    def history(self) -> list[NCOMState]:
        return list(self._history)
