"""Q11 — MCI tests."""
from services.mci import mci, mdl_bits

def test_compressing_payload_positive_mci():
    pre  = (b"random unique data " * 50)
    post = (b"aaa " * 50)   # highly compressible → shorter description length
    assert mci(pre, post) > 0

def test_bloated_payload_nonpositive_mci():
    pre  = b"core " * 20
    post = pre + b"UNNECESSARY " * 200
    assert mci(pre, post) == 0.0

def test_mdl_monotone():
    assert mdl_bits(b"") < mdl_bits(b"x" * 100)
