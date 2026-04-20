"""Q14 — SLSA/in-toto tests."""
from services.slsa import build_statement, verify_statement

def test_build_and_verify():
    data = b"the-release-bytes"
    stmt = build_statement("release.tar.gz", data)
    assert stmt["_type"].endswith("Statement/v1")
    assert verify_statement(stmt, data)

def test_tampered_bytes_fail():
    stmt = build_statement("x", b"AAA")
    assert not verify_statement(stmt, b"BBB")
