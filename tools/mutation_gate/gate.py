"""Mutation testing gate — mutation score threshold enforcement."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import hashlib


class MutationOperator(str, Enum):
    AOR = "arithmetic_operator_replacement"
    ROR = "relational_operator_replacement"
    LCR = "logical_connector_replacement"
    SVR = "scalar_value_replacement"
    SDL = "statement_deletion"


@dataclass
class MutationResult:
    operator: MutationOperator
    mutant_id: str
    killed: bool
    file: str
    line: int


@dataclass
class MutationGateReport:
    total: int
    killed: int
    score: float  # killed/total
    passed: bool
    threshold: float


def _mutant_id(file: str, line: int, op: MutationOperator) -> str:
    return hashlib.sha1(f"{file}:{line}:{op}".encode()).hexdigest()[:8]


class MutationGate:
    def __init__(self, threshold: float = 0.80):
        self._threshold = threshold
        self._results: list[MutationResult] = []

    def record(self, file: str, line: int, operator: MutationOperator, killed: bool) -> MutationResult:
        r = MutationResult(
            operator=operator,
            mutant_id=_mutant_id(file, line, operator),
            killed=killed,
            file=file,
            line=line,
        )
        self._results.append(r)
        return r

    def evaluate(self) -> MutationGateReport:
        total = len(self._results)
        if total == 0:
            return MutationGateReport(0, 0, 0.0, False, self._threshold)
        killed = sum(1 for r in self._results if r.killed)
        score = killed / total
        return MutationGateReport(total, killed, round(score, 4), score >= self._threshold, self._threshold)

    def survivors(self) -> list[MutationResult]:
        return [r for r in self._results if not r.killed]
