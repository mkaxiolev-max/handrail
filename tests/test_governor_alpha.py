"""Q16 — G2 + α tests."""
from services.governor2 import krippendorff_alpha_nominal, hic_escalation_required

def test_perfect_agreement_alpha_one():
    a = ["pass"]*10
    b = ["pass"]*10
    assert krippendorff_alpha_nominal(a,b) == 1.0

def test_random_disagreement_low_alpha():
    a = ["pass","block","pass","block","pass","block","pass","block"]
    b = ["block","pass","block","pass","block","pass","block","pass"]
    assert krippendorff_alpha_nominal(a,b) < 0.0
    assert hic_escalation_required(krippendorff_alpha_nominal(a,b))

def test_good_agreement_no_escalation():
    a = ["pass"]*9 + ["block"]
    b = ["pass"]*9 + ["block"]
    assert not hic_escalation_required(krippendorff_alpha_nominal(a,b))
