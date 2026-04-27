"""PRISM-Ω — multi-reality routing layer."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class Reality(str, Enum):
    LEXICON = "lexicon"
    ALEXANDRIA = "alexandria"
    SAN = "san"
    OMEGA = "omega"


@dataclass
class RoutingDecision:
    intent: str
    primary: Reality
    secondaries: list[Reality]
    confidence: float
    rationale: str


INTENT_ROUTING: dict[str, Reality] = {
    "semantic": Reality.LEXICON,
    "knowledge": Reality.ALEXANDRIA,
    "territory": Reality.SAN,
    "self_modify": Reality.OMEGA,
    "certification": Reality.OMEGA,
    "voice": Reality.LEXICON,
    "memory": Reality.ALEXANDRIA,
    "claim": Reality.SAN,
}


class PRISMRouter:
    def __init__(self):
        self._decisions: list[RoutingDecision] = []

    def route(self, intent: str, context: dict | None = None) -> RoutingDecision:
        primary = INTENT_ROUTING.get(intent, Reality.ALEXANDRIA)
        secondaries = [r for r in Reality if r != primary][:2]
        confidence = 0.95 if intent in INTENT_ROUTING else 0.60
        decision = RoutingDecision(
            intent=intent,
            primary=primary,
            secondaries=secondaries,
            confidence=confidence,
            rationale=f"intent={intent} maps to {primary.value}",
        )
        self._decisions.append(decision)
        return decision

    def decision_count(self) -> int:
        return len(self._decisions)

    def last_decision(self) -> RoutingDecision | None:
        return self._decisions[-1] if self._decisions else None
