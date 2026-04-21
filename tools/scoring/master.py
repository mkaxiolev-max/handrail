"""MASTER scorer — AXIOLEV Holdings LLC © 2026"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, List

@dataclass
class Sub:
    key: str; name: str; score: float; weight: float

@dataclass
class Instrument:
    id: str; name: str; score: float; weight_v21: float; weight_v30: float
    subs: List[Sub] | None = None

CURRENT = [
    Instrument("I1","Super-Omega v2", 88.02, 0.15, 0.15),
    Instrument("I2","Omega Intelligence v2", 83.22, 0.2, 0.2),
    Instrument("I3","UOIE v2", 84.60, 0.2, 0.175),
    Instrument("I4","GPX-Ω", 86.80, 0.3, 0.275),
    Instrument("I5","SAQ", 88.50, 0.15, 0.15),
    Instrument("I6","Ω-Logos", 88.65, 0.0, 0.1, subs=[
        Sub("C1","Gnoseogenic knowledge-birth", 87, 0.2),
        Sub("C2","Constitutive non-violation", 94, 0.25),
        Sub("C3","Action–knowledge symmetry", 86, 0.2),
        Sub("C4","Oracle-completeness", 81, 0.15),
        Sub("C5","Boundary-recognition (kenosis)", 92, 0.2),
    ]),
]

def score_i6(subs: List[Sub]) -> float:
    return round(sum(s.score * s.weight for s in subs), 2)

def master(insts: List[Instrument], version: str) -> float:
    k = "weight_v21" if version == "v2.1" else "weight_v30"
    return round(sum(i.score * getattr(i, k) for i in insts), 2)

def report() -> Dict:
    i6 = next(i for i in CURRENT if i.id=="I6")
    i6.score = score_i6(i6.subs)
    return {
        "v2_1": {"master": master(CURRENT, "v2.1")},
        "v3_0": {"master": master(CURRENT, "v3.0")},
        "instruments": [
            {"id": i.id, "name": i.name, "score": i.score,
             "weight_v21": i.weight_v21, "weight_v30": i.weight_v30,
             "subs": [asdict(s) for s in (i.subs or [])]}
            for i in CURRENT
        ],
    }

if __name__ == "__main__":
    import json
    print(json.dumps(report(), indent=2))
