"""Failure taxonomy — AXIOLEV Holdings LLC © 2026.
7 classes per Ω-Logos spec. Every runtime event maps to at most one class."""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict
import time

class Class(str, Enum):
    EPISTEMIC_ERROR      = "epistemic_error"
    EXECUTION_ERROR      = "execution_error"
    POLICY_VIOLATION     = "policy_violation"
    HALLUCINATION        = "hallucination"
    DRIFT                = "drift"
    ENVIRONMENT_FAILURE  = "environment_failure"
    ORACLE_FAILURE       = "oracle_failure"

@dataclass
class Counter:
    counts: Dict[Class, int] = field(default_factory=lambda: {c: 0 for c in Class})
    last_ts: Dict[Class, float] = field(default_factory=dict)

    def record(self, cls: Class) -> None:
        self.counts[cls] = self.counts.get(cls, 0) + 1
        self.last_ts[cls] = time.time()

    def distribution(self) -> Dict[str, int]:
        return {c.value: self.counts.get(c, 0) for c in Class}

COUNTER = Counter()
