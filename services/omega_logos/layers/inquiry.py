"""Inquiry layer — hypothesis graph, contradictions, confidence intervals.
AXIOLEV Holdings LLC © 2026. (Maps to I₆.C1 — contradiction_surface_rate + epistemic_gap_detection.)"""
from dataclasses import dataclass, field
from typing import List, Dict, Tuple

@dataclass
class Claim:
    id: str
    text: str
    confidence: float   # 0..1
    sources: List[str] = field(default_factory=list)

@dataclass
class Contradiction:
    a: str; b: str; severity: float

class HypothesisGraph:
    def __init__(self):
        self.claims: Dict[str, Claim] = {}
        self.contradictions: List[Contradiction] = []

    def add(self, c: Claim) -> None:
        self.claims[c.id] = c

    def detect_contradictions(self, pairs: List[Tuple[str, str]]) -> None:
        for a, b in pairs:
            ca, cb = self.claims.get(a), self.claims.get(b)
            if ca and cb:
                sev = abs(ca.confidence - cb.confidence)
                self.contradictions.append(Contradiction(a=a, b=b, severity=sev))

    def summary(self) -> Dict:
        return {
            "claim_count": len(self.claims),
            "contradictions": [c.__dict__ for c in self.contradictions],
            "avg_confidence": round(sum(c.confidence for c in self.claims.values()) / max(1, len(self.claims)), 3),
        }
