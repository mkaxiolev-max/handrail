"""C15 — CPS L0–L4 risk tiering tests. I7."""
from services.cps_risk_tiering.tiering import (
    classify_op, RiskTier, required_safeguards, tier_from_int, TIER_SAFEGUARDS,
)


def test_l0_no_safeguards():
    assert required_safeguards(RiskTier.L0) == []


def test_l4_has_quorum():
    assert "quorum_2of3" in required_safeguards(RiskTier.L4)


def test_stripe_is_l3():
    r = classify_op("stripe.get_balance")
    assert r.tier == RiskTier.L3
    assert r.yubikey_required is True


def test_gov_is_l4():
    r = classify_op("gov.record_decision")
    assert r.tier == RiskTier.L4
    assert r.quorum_required is True


def test_fs_is_l1():
    r = classify_op("fs.read")
    assert r.tier == RiskTier.L1
    assert r.yubikey_required is False


def test_classify_unknown_domain():
    r = classify_op("custom.op")
    assert isinstance(r.tier, RiskTier)


def test_tier_from_int():
    assert tier_from_int(0) == RiskTier.L0
    assert tier_from_int(4) == RiskTier.L4


def test_all_tiers_have_safeguard_entries():
    for tier in RiskTier:
        assert tier in TIER_SAFEGUARDS
