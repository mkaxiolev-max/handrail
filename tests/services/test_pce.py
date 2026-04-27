"""C02 — MISSING-003: Proof-Carrying Execution tests. I7."""
from services.proof_carrying_execution.pce import PCEExecutor, ExecutionProof


def test_pce_produces_proof():
    e = PCEExecutor()
    _, proof = e.execute_with_proof("op1", [1, 2, 3], sum)
    assert isinstance(proof, ExecutionProof)


def test_pce_proof_is_verifiable():
    e = PCEExecutor()
    input_data = {"x": 42}
    result, proof = e.execute_with_proof("op1", input_data, lambda d: d["x"] * 2)
    assert e.verify_proof(proof, input_data, result)


def test_pce_tampered_result_fails():
    e = PCEExecutor()
    input_data = 10
    result, proof = e.execute_with_proof("op1", input_data, lambda x: x + 1)
    assert not e.verify_proof(proof, input_data, result + 999)


def test_pce_tampered_input_fails():
    e = PCEExecutor()
    result, proof = e.execute_with_proof("op1", 5, lambda x: x)
    assert not e.verify_proof(proof, 6, result)


def test_pce_proof_has_unique_id():
    e = PCEExecutor()
    _, p1 = e.execute_with_proof("a", 1, lambda x: x)
    _, p2 = e.execute_with_proof("b", 2, lambda x: x)
    assert p1.proof_id != p2.proof_id


def test_pce_chain_tracks_all_proofs():
    e = PCEExecutor()
    for i in range(5):
        e.execute_with_proof(f"op{i}", i, lambda x: x)
    assert e.chain_length() == 5


def test_pce_proof_has_timestamp():
    e = PCEExecutor()
    _, p = e.execute_with_proof("t", "x", str)
    assert "T" in p.timestamp
