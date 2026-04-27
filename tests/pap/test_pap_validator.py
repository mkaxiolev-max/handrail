from services.pap.validator import validate_pap_resource
from services.pap.models import PAPClaim, EpistemicType


def test_valid_resource_passes(clean_resource):
    ok, reasons = validate_pap_resource(clean_resource)
    assert ok, f"expected pass; got reasons={reasons}"


def test_action_without_handrail_fails(make_resource):
    r = make_resource(handrail_required=False)
    ok, reasons = validate_pap_resource(r)
    assert not ok
    assert any("S2" in r_ for r_ in reasons)


def test_missing_identity_fails(make_resource):
    r = make_resource(skip_identity=True)
    # Identity has empty strings; merkle is still valid but identity check fails
    ok, reasons = validate_pap_resource(r)
    assert not ok
    assert any("S7" in r_ for r_ in reasons)


def test_h_with_empty_t_fails(make_resource):
    r = make_resource(claims=[], evidence=[])
    ok, reasons = validate_pap_resource(r)
    assert not ok
    assert any("S1" in r_ for r_ in reasons)
