import pytest
from services.nvir import (
    Candidate, NovelyOracle, ValidityOracle, IrreducibilityOracle,
    NvirScorer, EvolutionaryLoop, run_generation,
)

def test_novelty_empty_corpus():
    n=NovelyOracle(); c=Candidate("x","hello world foo bar"); assert n.novelty(c)==1.0

def test_novelty_duplicate():
    n=NovelyOracle(corpus=["hello world foo bar"])
    c=Candidate("x","hello world foo bar"); assert n.novelty(c)==0.0

def test_validity_passes():
    v=ValidityOracle(lambda s:"valid" in s)
    c=Candidate("x","this is valid"); assert v.check(c) is True

def test_validity_fails():
    v=ValidityOracle(lambda s:False)
    c=Candidate("x","any"); assert v.check(c) is False

def test_nvir_zero_on_invalid():
    v=ValidityOracle(lambda s:False); n=NovelyOracle(); i=IrreducibilityOracle()
    c=Candidate("x","test"); assert NvirScorer(v,n,i).score(c)==0.0

def test_nvir_positive_on_valid():
    v=ValidityOracle(lambda s:True); n=NovelyOracle(); i=IrreducibilityOracle()
    c=Candidate("x","novel content with meaningful structure and detail here")
    assert NvirScorer(v,n,i).score(c)>0

def test_run_generation():
    result=run_generation(lambda s:f"candidate {len(s)}",lambda s:"candidate" in s,n_steps=10)
    assert result["n_candidates"]==10 and "mean_nvir" in result
