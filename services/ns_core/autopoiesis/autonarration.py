"""Autonarration — reads Alexandria ledger, writes to feed_items. Never writes back to ledger."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List


_FEED_FILE = os.environ.get("FEED_ITEMS_PATH", "/tmp/ns_feed_items.jsonl")


def narrate_receipts(receipts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert receipt list to feed items. Read-only on receipts."""
    items = []
    for r in receipts:
        item = {
            "feed_id": r.get("receipt_id", "unknown"),
            "summary": f"Op: {r.get('operation', r.get('op', 'unknown'))}",
            "ts": r.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "ok": r.get("ok", True),
        }
        items.append(item)
        _write_feed_item(item)
    return items


def _write_feed_item(item: Dict[str, Any]) -> None:
    """Append to feed_items — never writes to Alexandria ledger."""
    try:
        with open(_FEED_FILE, "a") as f:
            f.write(json.dumps(item) + "\n")
    except Exception:
        pass
