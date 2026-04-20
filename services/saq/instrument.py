"""SAQ instrument. © 2026 AXIOLEV Holdings LLC"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict

@dataclass
class SAQScore:
    receipt_chain: float=0.0; hamiltonian_gate: float=0.0
    reversibility: float=0.0; three_realities: float=0.0

    @property
    def composite(self) -> float:
        return 0.25*(self.receipt_chain+self.hamiltonian_gate+self.reversibility+self.three_realities)

class ReceiptChainMetric:
    def score(self, e: Dict) -> float:
        s=0
        if e.get("alexandria_structured"):    s+=25
        if e.get("merkle_committed"):         s+=20
        if e.get("forward_secure_mac"):       s+=15
        if e.get("witness_cosign_count",0)>=3:s+=20
        if e.get("rfc9162_compliant"):        s+=10
        if e.get("fiat_crypto_verified"):     s+=10
        return min(s,100)

class HamiltonianGateMetric:
    def score(self, e: Dict) -> float:
        s=0
        if e.get("dignity_kernel_present"):   s+=30
        if e.get("mandatory_routing"):        s+=25
        if e.get("tla_verified"):             s+=20
        s+=int(15*min(e.get("runtime_assertion_coverage",0.0),1.0))
        if e.get("bypass_impossible"):        s+=10
        return min(s,100)

class ReversibilityMetric:
    def score(self, e: Dict) -> float:
        s=int(e.get("reversible_transitions_fraction",0.0)*80)
        if e.get("replay_operator_sound"):    s+=10
        if e.get("counterfactual_reachable"): s+=10
        return min(s,100)

class ThreeRealitiesMetric:
    def score(self, e: Dict) -> float:
        s=0
        if e.get("lexicon_distinct"):         s+=25
        if e.get("alexandria_distinct"):      s+=25
        if e.get("san_distinct"):             s+=25
        if e.get("reconstruction_sound"):     s+=25
        return min(s,100)

def compute_saq(evidence: Dict) -> SAQScore:
    return SAQScore(
        receipt_chain=float(ReceiptChainMetric().score(evidence)),
        hamiltonian_gate=float(HamiltonianGateMetric().score(evidence)),
        reversibility=float(ReversibilityMetric().score(evidence)),
        three_realities=float(ThreeRealitiesMetric().score(evidence)),
    )
