"""Autonarration must never write to the ledger — only feed_items."""
import os, json, tempfile
from autopoiesis.autonarration import narrate_receipts


def test_narration_produces_feed_items():
    receipts = [
        {"receipt_id": "r1", "operation": "test.op", "ok": True, "timestamp": "2026-01-01T00:00:00Z"},
        {"receipt_id": "r2", "operation": "test.op2", "ok": False, "timestamp": "2026-01-01T00:01:00Z"},
    ]
    items = narrate_receipts(receipts)
    assert len(items) == 2
    assert items[0]["feed_id"] == "r1"
    assert items[1]["feed_id"] == "r2"


def test_narration_does_not_write_to_ledger(tmp_path):
    """No Alexandria ledger files should be created by autonarration."""
    import autopoiesis.autonarration as m
    original = m._FEED_FILE
    m._FEED_FILE = str(tmp_path / "feed.jsonl")
    try:
        receipts = [{"receipt_id": "rx1", "operation": "narrate.test", "ok": True}]
        narrate_receipts(receipts)
        # Feed file written OK
        assert os.path.exists(m._FEED_FILE)
        # No Alexandria ledger written
        alex_ledger = "/Volumes/NSExternal/ALEXANDRIA/receipts/boot_receipts.jsonl"
        if os.path.exists(alex_ledger):
            with open(alex_ledger) as f:
                before_size = len(f.read())
            narrate_receipts(receipts)
            with open(alex_ledger) as f:
                after_size = len(f.read())
            assert after_size == before_size, "autonarration must not write to ledger"
    finally:
        m._FEED_FILE = original


def test_narration_return_shape():
    receipts = [{"receipt_id": "rz1", "operation": "shape.test", "ok": True}]
    items = narrate_receipts(receipts)
    item = items[0]
    assert "feed_id" in item
    assert "summary" in item
    assert "ts" in item
    assert "ok" in item
