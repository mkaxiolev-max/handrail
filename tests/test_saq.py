import pytest
from services.saq import SAQScore, ReceiptChainMetric, HamiltonianGateMetric, ReversibilityMetric, ThreeRealitiesMetric, compute_saq

def test_composite_perfect():   assert SAQScore(100,100,100,100).composite==100.0
def test_composite_mixed():     assert SAQScore(80,60,70,90).composite==pytest.approx(75.0)
def test_receipt_empty():       assert ReceiptChainMetric().score({})==0
def test_receipt_full():
    assert ReceiptChainMetric().score({"alexandria_structured":True,"merkle_committed":True,
        "forward_secure_mac":True,"witness_cosign_count":5,"rfc9162_compliant":True,"fiat_crypto_verified":True})==100
def test_hamiltonian_partial():
    assert 50<=HamiltonianGateMetric().score({"dignity_kernel_present":True,"mandatory_routing":True,"runtime_assertion_coverage":0.8})<=100
def test_reversibility():
    assert ReversibilityMetric().score({"reversible_transitions_fraction":0.9,"replay_operator_sound":True,"counterfactual_reachable":True})>=90
def test_three_realities():
    assert ThreeRealitiesMetric().score({"lexicon_distinct":True,"alexandria_distinct":True,"san_distinct":True,"reconstruction_sound":True})==100
def test_compute_saq_ns():
    saq=compute_saq({"alexandria_structured":True,"merkle_committed":True,"witness_cosign_count":3,
        "dignity_kernel_present":True,"mandatory_routing":True,"tla_verified":True,
        "runtime_assertion_coverage":0.85,"bypass_impossible":True,
        "reversible_transitions_fraction":0.80,"replay_operator_sound":True,
        "lexicon_distinct":True,"alexandria_distinct":True,"san_distinct":True,"reconstruction_sound":True})
    assert 80<=saq.composite<=95
