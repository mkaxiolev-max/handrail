from __future__ import annotations
from dataclasses import dataclass
from typing import List
import math

@dataclass
class EWMADrift:
    lam: float=0.2; baseline: float=0.0; baseline_sigma: float=1.0; ewma: float=0.0
    def __post_init__(self): self.ewma=self.baseline
    def update(self, x: float) -> float:
        self.ewma=self.lam*x+(1-self.lam)*self.ewma
        return (self.ewma-self.baseline)/self.baseline_sigma if self.baseline_sigma>0 else 0.0

def PSI(baseline: List[float], current: List[float], n_bins: int=10) -> float:
    if not baseline or not current: return 0.0
    combined=sorted(baseline+current)
    edges=[combined[int(i*len(combined)/n_bins)] for i in range(1,n_bins)]
    def bin_pct(xs):
        counts=[0]*n_bins
        for x in xs:
            b=0
            while b<len(edges) and x>edges[b]: b+=1
            counts[b]+=1
        return [(c+1e-6)/len(xs) for c in counts]
    p_base=bin_pct(baseline); p_cur=bin_pct(current)
    return sum((q-p)*math.log(q/p) for p,q in zip(p_base,p_cur))
