"""Aletheia-Ω — 5-step constitutional self-improvement loop."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import time


class AletheiaStep(str, Enum):
    OBSERVE = "observe"      # 1. Gather evidence
    ANALYZE = "analyze"      # 2. Identify gaps
    HYPOTHESIZE = "hypothesize"  # 3. Propose improvements
    TEST = "test"            # 4. Verify proposal
    INTEGRATE = "integrate"  # 5. Commit accepted improvement


@dataclass
class AletheiaState:
    step: AletheiaStep
    cycle: int
    evidence: list[str]
    gaps: list[str]
    hypothesis: str
    test_result: bool | None
    integrated: bool
    ts: float = field(default_factory=time.time)

    @property
    def receipt_hash(self) -> str:
        data = f"{self.cycle}:{self.step}:{self.hypothesis}:{self.ts}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


class AletheiaOmegaLoop:
    def __init__(self):
        self._cycle = 0
        self._states: list[AletheiaState] = []
        self._current: AletheiaState | None = None

    def start_cycle(self) -> AletheiaState:
        self._cycle += 1
        s = AletheiaState(
            step=AletheiaStep.OBSERVE,
            cycle=self._cycle,
            evidence=[], gaps=[], hypothesis="",
            test_result=None, integrated=False,
        )
        self._current = s
        self._states.append(s)
        return s

    def observe(self, evidence: list[str]) -> AletheiaState:
        assert self._current and self._current.step == AletheiaStep.OBSERVE
        self._current.evidence = evidence
        self._current.step = AletheiaStep.ANALYZE
        return self._current

    def analyze(self, gaps: list[str]) -> AletheiaState:
        assert self._current and self._current.step == AletheiaStep.ANALYZE
        self._current.gaps = gaps
        self._current.step = AletheiaStep.HYPOTHESIZE
        return self._current

    def hypothesize(self, hypothesis: str) -> AletheiaState:
        assert self._current and self._current.step == AletheiaStep.HYPOTHESIZE
        self._current.hypothesis = hypothesis
        self._current.step = AletheiaStep.TEST
        return self._current

    def test(self, passed: bool) -> AletheiaState:
        assert self._current and self._current.step == AletheiaStep.TEST
        self._current.test_result = passed
        self._current.step = AletheiaStep.INTEGRATE
        return self._current

    def integrate(self, accept: bool) -> AletheiaState:
        assert self._current and self._current.step == AletheiaStep.INTEGRATE
        self._current.integrated = accept and (self._current.test_result is True)
        return self._current

    def cycle_count(self) -> int:
        return self._cycle

    def integrated_count(self) -> int:
        return sum(1 for s in self._states if s.integrated)

    def history(self) -> list[AletheiaState]:
        return list(self._states)
