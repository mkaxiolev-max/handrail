"""14 tests -- witness cosigning triad. AXIOLEV Holdings LLC (c) 2026."""
from services.witness import (
    STH, cosign, verify, cosign_triad, verify_cosigned,
    consistency_ok, sth_hash,
)

def _sth(size=10, root="a"*64, ts=1_700_000_000_000, prev=None):
    return STH(tree_size=size, root_hash=root, timestamp=ts, prev_root_hash=prev)

def test_1_sth_hash_deterministic():
    s = _sth(); assert sth_hash(s) == sth_hash(s)

def test_2_sth_hash_changes_with_root():
    s1 = _sth(root="a"*64); s2 = _sth(root="b"*64)
    assert sth_hash(s1) != sth_hash(s2)

def test_3_single_cosign_verifies():
    s = _sth(); c = cosign(s, "witness_alpha"); assert verify(c, s)

def test_4_cosign_rejects_wrong_sth():
    s1 = _sth(size=10); s2 = _sth(size=11)
    c = cosign(s1, "witness_alpha"); assert not verify(c, s2)

def test_5_unknown_witness_raises():
    s = _sth()
    try:
        cosign(s, "witness_rogue"); assert False
    except ValueError:
        pass

def test_6_triad_produces_three_signatures():
    s = _sth(); cs = cosign_triad(s); assert len(cs.cosignatures) == 3

def test_7_triad_meets_quorum_two_of_three():
    s = _sth(); cs = cosign_triad(s, quorum=2); assert cs.valid()

def test_8_triad_verifies_end_to_end():
    s = _sth(); cs = cosign_triad(s); assert verify_cosigned(cs)

def test_9_tampered_root_fails_verification():
    s = _sth(root="a"*64); cs = cosign_triad(s)
    tampered = STH(tree_size=s.tree_size, root_hash="c"*64, timestamp=s.timestamp, prev_root_hash=s.prev_root_hash)
    cs2 = type(cs)(sth=tampered, cosignatures=cs.cosignatures, quorum=cs.quorum)
    assert not verify_cosigned(cs2)

def test_10_consistency_monotone_size():
    prev = _sth(size=10, root="a"*64); curr = _sth(size=12, root="b"*64, prev="a"*64)
    assert consistency_ok(prev, curr)

def test_11_consistency_rejects_shrink():
    prev = _sth(size=12, root="a"*64); curr = _sth(size=10, root="b"*64, prev="a"*64)
    assert not consistency_ok(prev, curr)

def test_12_consistency_rejects_broken_chain():
    prev = _sth(size=10, root="a"*64); curr = _sth(size=12, root="b"*64, prev="WRONG"*12+"aaaa")
    assert not consistency_ok(prev, curr)

def test_13_same_size_same_root_allowed():
    prev = _sth(size=10, root="a"*64); curr = _sth(size=10, root="a"*64, prev="a"*64)
    assert consistency_ok(prev, curr)

def test_14_quorum_three_of_three_enforced_when_requested():
    s = _sth(); cs = cosign_triad(s, quorum=3)
    assert cs.valid(); assert verify_cosigned(cs)
