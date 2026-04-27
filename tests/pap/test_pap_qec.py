from services.pap.qec import detect_qec_syndromes
from services.pap.models import PAPClaim, EpistemicType


def test_clean_resource_has_no_syndromes(clean_resource):
    out = detect_qec_syndromes(clean_resource)
    assert out == [], f"expected clean; got {[s.syndrome for s in out]}"


def test_S2_detected_on_handrail_bypass(make_resource):
    r = make_resource(handrail_required=False)
    out = detect_qec_syndromes(r)
    assert any(s.syndrome == "S2" for s in out)


def test_S7_detected_on_missing_identity(make_resource):
    r = make_resource(skip_identity=True)
    out = detect_qec_syndromes(r)
    assert any(s.syndrome == "S7" for s in out)


def test_S8_detected_on_merkle_mutation(clean_resource):
    clean_resource.H.summary = "Mutated"
    out = detect_qec_syndromes(clean_resource)
    assert any(s.syndrome == "S8" for s in out)


def test_S10_detected_on_persuasion_without_truth(make_resource):
    r = make_resource(persuasion_flags=["urgency"], claims=[], evidence=[])
    out = detect_qec_syndromes(r)
    assert any(s.syndrome == "S10" for s in out)
