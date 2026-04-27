from services.pap.canon_bridge import (
    triadic_canon_check, can_promote_to_canon_via_pap,
)


def test_triadic_min_at_95_eligible():
    eligible, tmin, blocker = triadic_canon_check(95.0, 95.0, 95.0)
    assert eligible
    assert tmin == 95.0
    assert blocker is None


def test_triadic_min_below_95_blocks():
    eligible, tmin, blocker = triadic_canon_check(100.0, 100.0, 94.0)
    assert not eligible
    assert tmin == 94.0
    assert blocker == "PAP"


def test_blocking_track_ldr():
    eligible, tmin, blocker = triadic_canon_check(80.0, 100.0, 100.0)
    assert blocker == "LDR"


def test_blocking_track_omega():
    eligible, tmin, blocker = triadic_canon_check(100.0, 70.0, 100.0)
    assert blocker == "OMEGA_GNOSEO"


def test_dual_aletheion_required():
    ok, reason = can_promote_to_canon_via_pap("DENY", "ALLOW", 100, 100, 100)
    assert not ok
    assert "logos" in reason


def test_full_clearance_promotes():
    ok, reason = can_promote_to_canon_via_pap("ALLOW", "ALLOW", 96, 97, 98)
    assert ok
