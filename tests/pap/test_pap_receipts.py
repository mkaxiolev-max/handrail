import os, tempfile
from pathlib import Path


def test_pap_receipt_chains_and_writes_to_disk():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["PAP_RECEIPT_ROOT"] = tmp
        # Reload to pick up env var
        import importlib, services.pap.receipts as receipts
        importlib.reload(receipts)
        r1 = receipts.write_pap_receipt(
            resource_id="uri://t/1", decision="ADMIT", pap_score=92.0,
            aletheion_receipt_refs=["aletheion://x"],
        )
        r2 = receipts.write_pap_receipt(
            resource_id="uri://t/2", decision="ADMIT", pap_score=93.0,
        )
        # Both written
        assert any(Path(tmp).rglob(f"{r1.receipt_id}.json"))
        assert any(Path(tmp).rglob(f"{r2.receipt_id}.json"))
        # Hashes differ
        assert r1.hash != r2.hash
