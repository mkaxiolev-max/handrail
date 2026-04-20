# -*- coding: utf-8 -*-
# AXIOLEV Holdings LLC © 2026 — Q9 ceiling uplift
"""NVIR Verifier — admits candidates by novelty × validity × non-triviality."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, List, Set

@dataclass
class NVIRCandidate:
    formula: str
    score:   float

class NVIRVerifier:
    def __init__(self, known: Set[str]) -> None:
        self._known = set(known)

    def is_novel(self, c: NVIRCandidate) -> bool:
        return c.formula not in self._known

    def is_valid(self, c: NVIRCandidate, oracle: Callable[[str], bool]) -> bool:
        return oracle(c.formula)

    def is_nontrivial(self, c: NVIRCandidate) -> bool:
        return len(c.formula.strip()) > 3 and c.score > 0.0

    def admit(self, c: NVIRCandidate, oracle: Callable[[str], bool]) -> bool:
        return self.is_novel(c) and self.is_valid(c, oracle) and self.is_nontrivial(c)

def nvir_rate(candidates: List[NVIRCandidate],
              verifier: NVIRVerifier,
              oracle: Callable[[str], bool]) -> float:
    if not candidates: return 0.0
    admitted = sum(1 for c in candidates if verifier.admit(c, oracle))
    return admitted / len(candidates)
