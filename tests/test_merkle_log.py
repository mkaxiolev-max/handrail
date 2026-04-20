"""Q2 — Merkle log tests."""
from services.alex_merkle import MerkleLog

def test_append_grows_size():
    log = MerkleLog()
    for i in range(10):
        log.append(f"entry-{i}".encode())
    assert log.size() == 10

def test_inclusion_proof_roundtrip():
    log = MerkleLog()
    for i in range(16):
        log.append(f"e-{i}".encode())
    root = log.root()
    for i in range(16):
        proof = log.inclusion_proof(i)
        assert log.verify_inclusion(f"e-{i}".encode(), i, proof, root)

def test_tampered_entry_fails_proof():
    log = MerkleLog()
    for i in range(8): log.append(f"x-{i}".encode())
    proof = log.inclusion_proof(3)
    assert not log.verify_inclusion(b"WRONG", 3, proof, log.root())
