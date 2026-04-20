"""NVIR generation loop. © 2026 AXIOLEV Holdings LLC"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, List, Dict, Optional
import random, zlib

@dataclass
class Candidate:
    artifact_id: str; content: str; score: float=0.0; validity: bool=False
    novelty: float=0.0; irreducibility: float=0.0; utility: float=0.0
    nvir: float=0.0; generation: int=0

class ValidityOracle:
    def __init__(self, checker: Callable[[str], bool]): self.checker = checker
    def check(self, c: Candidate) -> bool:
        try: c.validity = bool(self.checker(c.content))
        except: c.validity = False
        return c.validity

class NovelyOracle:
    def __init__(self, corpus=None, tau_nov: float=0.35):
        self.corpus = corpus or []; self.tau_nov = tau_nov

    @staticmethod
    def _shingles(s: str, n: int=3) -> set:
        tokens = s.lower().split()
        return set(" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)) or {s.lower()}

    def distance(self, a: str, b: str) -> float:
        sa,sb = self._shingles(a),self._shingles(b)
        if not sa or not sb: return 1.0
        return 1.0 - (len(sa&sb)/len(sa|sb))

    def novelty(self, c: Candidate) -> float:
        if not self.corpus: c.novelty = 1.0; return 1.0
        dists = [self.distance(c.content,e) for e in self.corpus]
        c.novelty = min(dists) if dists else 1.0; return c.novelty

class IrreducibilityOracle:
    def irreducibility(self, c: Candidate) -> float:
        s = c.content.encode()
        if not s: return 0.0
        ratio = len(zlib.compress(s,level=9))/max(len(s),1)
        c.irreducibility = min(ratio,1.0); return c.irreducibility

class NvirScorer:
    def __init__(self, validity, novelty, irreducibility,
                 alpha=0.4, beta=0.3, gamma=0.3):
        self.validity=validity; self.novelty=novelty
        self.irreducibility=irreducibility
        self.alpha=alpha; self.beta=beta; self.gamma=gamma

    def score(self, c: Candidate, utility_fn=None) -> float:
        if not self.validity.check(c): c.nvir=0.0; return 0.0
        nov = self.novelty.novelty(c); irr = self.irreducibility.irreducibility(c)
        util = utility_fn(c) if utility_fn else 0.5; c.utility = util
        c.nvir = self.alpha*nov + self.beta*irr + self.gamma*util
        c.score = c.nvir; return c.nvir

@dataclass
class Island:
    island_id: int; population: List[Candidate]=field(default_factory=list); pop_cap: int=1000
    def add(self, c: Candidate):
        self.population.append(c)
        if len(self.population) > self.pop_cap:
            self.population.sort(key=lambda x:-x.nvir)
            self.population = self.population[:self.pop_cap]
    def top_k(self, k=2): return sorted(self.population,key=lambda x:-x.nvir)[:k]

class EvolutionaryLoop:
    def __init__(self, n_islands=10, pop_cap=1000):
        self.islands=[Island(island_id=i,pop_cap=pop_cap) for i in range(n_islands)]
        self.step=0

    def migrate(self):
        n=len(self.islands)
        for i in range(n):
            for c in self.islands[i].top_k(2):
                self.islands[(i+1)%n].add(c)

    def reseed(self):
        all_pop=[c for isl in self.islands for c in isl.population]
        if len(all_pop)<10: return
        elites=sorted(all_pop,key=lambda x:-x.nvir)[:max(1,len(all_pop)//10)]
        for isl in self.islands:
            sp=sorted(isl.population,key=lambda x:x.nvir); mid=len(sp)//2
            isl.population=sp[mid:]+elites[:max(1,mid)]

    def record(self, candidate: Candidate, island_idx: int=0):
        self.islands[island_idx%len(self.islands)].add(candidate)
        self.step+=1
        if self.step%500==0: self.migrate()
        if self.step%2000==0: self.reseed()

def run_generation(proposer, validity_checker, n_steps=100, seed_corpus=None) -> Dict:
    vo=ValidityOracle(validity_checker); no=NovelyOracle(corpus=seed_corpus or [])
    io=IrreducibilityOracle(); scorer=NvirScorer(vo,no,io)
    loop=EvolutionaryLoop(n_islands=3,pop_cap=50)
    for step in range(n_steps):
        idx=step%len(loop.islands)
        best=[c.content for c in loop.islands[idx].top_k(2)]
        try: new=proposer(best)
        except: continue
        c=Candidate(artifact_id=f"c{step}",content=new,generation=step)
        scorer.score(c)
        if c.validity: no.corpus.append(c.content)
        loop.record(c,idx)
    all_c=[c for isl in loop.islands for c in isl.population]
    valid=[c for c in all_c if c.validity]
    return {"n_candidates":len(all_c),"n_valid":len(valid),
            "n_novel_valid":sum(1 for c in valid if c.novelty>no.tau_nov),
            "mean_nvir":sum(c.nvir for c in all_c)/max(len(all_c),1),
            "mean_nvir_valid":sum(c.nvir for c in valid)/max(len(valid),1),
            "top_artifacts":[{"id":c.artifact_id,"nvir":c.nvir} for c in
                              sorted(valid,key=lambda x:-x.nvir)[:5]]}
