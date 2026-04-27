"""Hash-chained JSONL audit log (RFC 9162-style leaf hash)."""
from __future__ import annotations
import hashlib, json, pathlib, secrets
from datetime import datetime, timezone

GENESIS = "0"*64
RECEIPT_TYPES = {
    "ALET_CONTROL_CLASSIFICATION_RECEIPT",
    "ALET_CONTROL_ATOM_RECEIPT",
    "ALET_INFLUENCE_CHAIN_RECEIPT",
    "ALET_CONCERN_WASTE_RECEIPT",
    "ALET_DAILY_CONTROL_SUMMARY",
    "ALET_WEEKLY_DELETION_AUDIT",
    "ALET_CONTROL_DRIFT_EVENT",
    "ALET_FALSE_CONTROL_COLLAPSE",
}

def _canon(d: dict) -> bytes:
    return json.dumps(d, sort_keys=True, separators=(",",":")).encode()

def leaf_hash(canon: bytes) -> str:
    return hashlib.sha256(b"\x00"+canon).hexdigest()

def new_receipt_id() -> str:
    return "rcp_" + secrets.token_hex(6)

def append(path: pathlib.Path, kind: str, payload: dict) -> dict:
    if kind not in RECEIPT_TYPES:
        raise ValueError(f"unknown kind {kind}")
    prev = GENESIS
    if path.exists() and path.stat().st_size > 0:
        prev = json.loads(path.read_text().splitlines()[-1])["receipt_hash"]
    rec = {
        "receipt_id": new_receipt_id(),
        "timestamp":  datetime.now(tz=timezone.utc).isoformat(),
        "kind":       kind,
        "prev_hash":  prev,
        "payload":    payload,
    }
    rec["receipt_hash"] = leaf_hash(_canon(rec))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec

def verify(path: pathlib.Path) -> bool:
    if not path.exists(): return True
    prev = GENESIS
    for line in path.read_text().splitlines():
        r = json.loads(line); h = r.pop("receipt_hash")
        if r["prev_hash"] != prev or leaf_hash(_canon(r)) != h:
            return False
        prev = h
    return True
