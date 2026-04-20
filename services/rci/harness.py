"""RCI harness. © 2026 AXIOLEV Holdings LLC"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, List, Dict, Optional
import math

@dataclass
class EditRequest:
    edit_id: str; locus: str; old_value: str; new_value: str
    probe_prompts: List[str]=field(default_factory=list)
    paraphrase_probes: List[str]=field(default_factory=list)
    locality_probes: List[str]=field(default_factory=list)
    portability_probes: List[str]=field(default_factory=list)

@dataclass
class EditResult:
    edit_id: str; efficacy: float=0.0; generalization: float=0.0
    specificity: float=0.0; portability: float=0.0
    propagation_depth: int=0; constitutional_locality: float=1.0; rci: float=0.0

def harmonic_mean(values: List[float]) -> float:
    safe=[max(v,1e-9) for v in values]
    return len(safe)/sum(1/v for v in safe)

def compute_rci(r: EditResult) -> float:
    hm=harmonic_mean([r.efficacy,r.generalization,r.specificity])
    return hm*math.sqrt(max(r.portability,0.0))*(r.constitutional_locality**2)

@dataclass
class RciMetrics:
    n_edits: int=0; mean_rci: float=0.0; mean_efficacy: float=0.0
    mean_generalization: float=0.0; mean_specificity: float=0.0
    mean_portability: float=0.0; mean_propagation_depth: float=0.0
    constitutional_failures: int=0

    @classmethod
    def from_results(cls, results: List[EditResult]) -> "RciMetrics":
        if not results: return cls()
        return cls(n_edits=len(results),
            mean_rci=sum(r.rci for r in results)/len(results),
            mean_efficacy=sum(r.efficacy for r in results)/len(results),
            mean_generalization=sum(r.generalization for r in results)/len(results),
            mean_specificity=sum(r.specificity for r in results)/len(results),
            mean_portability=sum(r.portability for r in results)/len(results),
            mean_propagation_depth=sum(r.propagation_depth for r in results)/len(results),
            constitutional_failures=sum(1 for r in results if r.constitutional_locality<1.0))

class RciHarness:
    def __init__(self, probe_fn, edit_fn=None, invariant_checker=None):
        self.probe_fn=probe_fn; self.edit_fn=edit_fn
        self.invariant_checker=invariant_checker or (lambda:True)

    @staticmethod
    def _match(response: str, expected: str) -> float:
        return 1.0 if expected.lower() in response.lower() else 0.0

    def run_edit(self, req: EditRequest) -> EditResult:
        r=EditResult(edit_id=req.edit_id)
        pre_ok=self.invariant_checker()
        if self.edit_fn:
            try: self.edit_fn(req)
            except: r.rci=0.0; return r
        r.efficacy=(sum(self._match(self.probe_fn(p),req.new_value) for p in req.probe_prompts)
                    /len(req.probe_prompts)) if req.probe_prompts else 1.0
        r.generalization=(sum(self._match(self.probe_fn(p),req.new_value) for p in req.paraphrase_probes)
                          /len(req.paraphrase_probes)) if req.paraphrase_probes else r.efficacy
        r.specificity=(sum(1.0-self._match(self.probe_fn(p),req.new_value) for p in req.locality_probes)
                       /len(req.locality_probes)) if req.locality_probes else 1.0
        r.portability=(sum(self._match(self.probe_fn(p),req.new_value) for p in req.portability_probes)
                       /len(req.portability_probes)) if req.portability_probes else 0.5
        r.propagation_depth=min(5,int(r.portability*5))
        r.constitutional_locality=1.0 if (pre_ok and self.invariant_checker()) else 0.0
        r.rci=compute_rci(r); return r

    def run_batch(self, requests: List[EditRequest]) -> RciMetrics:
        return RciMetrics.from_results([self.run_edit(req) for req in requests])
