"""Autonomous Goal Formation — derives prioritized goals from context."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GoalStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    ACHIEVED = "achieved"
    ABANDONED = "abandoned"


class GoalPriority(int, Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class Goal:
    goal_id: str
    description: str
    priority: GoalPriority
    source: str
    status: GoalStatus = GoalStatus.PENDING
    context_keys: list[str] = field(default_factory=list)


class GoalRegistry:
    def __init__(self):
        self._goals: dict[str, Goal] = {}

    def form_goal(self, context: dict[str, Any]) -> Goal:
        # Derive goal from context keys — missing keys become goals
        missing = [k for k, v in context.items() if v is None or v == ""]
        priority = GoalPriority.HIGH if missing else GoalPriority.LOW
        desc = f"Resolve: {missing}" if missing else "Maintain current state"
        gid = f"goal_{len(self._goals):04d}"
        g = Goal(gid, desc, priority, source="auto", context_keys=list(context.keys()))
        self._goals[gid] = g
        return g

    def rank_goals(self) -> list[Goal]:
        return sorted(self._goals.values(), key=lambda g: g.priority.value)

    def update_status(self, goal_id: str, status: GoalStatus) -> None:
        if goal_id in self._goals:
            self._goals[goal_id].status = status

    def active_goals(self) -> list[Goal]:
        return [g for g in self._goals.values() if g.status == GoalStatus.ACTIVE]

    def pending_goals(self) -> list[Goal]:
        return [g for g in self._goals.values() if g.status == GoalStatus.PENDING]

    def all_goals(self) -> list[Goal]:
        return list(self._goals.values())
