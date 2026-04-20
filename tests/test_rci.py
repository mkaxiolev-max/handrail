import pytest
from services.rci import EditRequest, EditResult, RciMetrics, RciHarness, harmonic_mean, compute_rci

def test_harmonic_mean():
    assert harmonic_mean([1.0,1.0,1.0])==pytest.approx(1.0)
    assert harmonic_mean([0.5,0.5,0.5])==pytest.approx(0.5)

def test_compute_rci_perfect():
    r=EditResult("x",efficacy=1,generalization=1,specificity=1,portability=1,constitutional_locality=1)
    assert compute_rci(r)==pytest.approx(1.0)

def test_compute_rci_zero_cl():
    r=EditResult("x",efficacy=1,generalization=1,specificity=1,portability=1,constitutional_locality=0)
    assert compute_rci(r)==0.0

def test_harness_edit_flow():
    state={"v":"old"}
    harness=RciHarness(probe_fn=lambda p:state["v"], edit_fn=lambda req:state.update({"v":req.new_value}))
    r=harness.run_edit(EditRequest("e1","l1","old","new",probe_prompts=["q"],paraphrase_probes=["qp"],
                                   locality_probes=["ql"],portability_probes=["qd"]))
    assert r.efficacy==1.0

def test_metrics_from_results():
    results=[EditResult("a",efficacy=1,generalization=1,specificity=1,portability=1,constitutional_locality=1,rci=1.0),
             EditResult("b",efficacy=0.8,generalization=0.7,specificity=0.9,portability=0.5,constitutional_locality=1,rci=0.55)]
    m=RciMetrics.from_results(results)
    assert m.n_edits==2 and m.mean_rci==pytest.approx(0.775)
