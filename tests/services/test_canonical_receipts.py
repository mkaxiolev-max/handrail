"""C11 — MISSING-025: Six canonical receipts tests. I8."""
from services.canonical_receipts.receipts import ReceiptChain, ReceiptType, Receipt


def test_six_receipt_types_exist():
    assert len(list(ReceiptType)) == 6


def test_emit_first_principles():
    c = ReceiptChain()
    r = c.emit(ReceiptType.FIRST_PRINCIPLES, {"reason": "new cycle"})
    assert r.receipt_type == "first_principles"


def test_emit_deletion_proof():
    c = ReceiptChain()
    r = c.emit(ReceiptType.DELETION_PROOF, {"path": "x.py", "justification": "unused"})
    assert r.receipt_type == "deletion_proof"


def test_emit_all_six_types():
    c = ReceiptChain()
    for rt in ReceiptType:
        c.emit(rt, {"test": True})
    assert c.length() == 6


def test_chain_is_valid():
    c = ReceiptChain()
    c.emit(ReceiptType.FIRST_PRINCIPLES, {"x": 1})
    c.emit(ReceiptType.ALETHEIA_STATE, {"state": "active"})
    assert c.verify()


def test_chain_self_hash_is_sha256():
    c = ReceiptChain()
    r = c.emit(ReceiptType.EXTERNAL_EVENT, {"source": "voice"})
    assert r.self_hash.startswith("sha256:")


def test_chain_prev_hash_links_correctly():
    c = ReceiptChain()
    r1 = c.emit(ReceiptType.FIRST_PRINCIPLES, {})
    r2 = c.emit(ReceiptType.SIMPLIFICATION_DELTA, {})
    assert r2.prev_hash == r1.self_hash


def test_chain_genesis_for_first():
    c = ReceiptChain()
    r = c.emit(ReceiptType.CERTIFICATION_ARTIFACT, {"artifact": "report.json"})
    assert r.prev_hash == ReceiptChain.GENESIS
