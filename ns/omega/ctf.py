"""
axiolev-omega-ctf-v2
AXIOLEV Holdings LLC © 2026

Lineage Fabric receipt emitter. I5: SHA-256 hash-chain. I2: append-only.
"""
from __future__ import annotations
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_LEDGER = os.environ.get(
    "NS_ALEX_LEDGER",
    "/Volumes/NSExternal/ALEXANDRIA/ledger/ns_events.jsonl",
)
DEFAULT_CTF = os.environ.get(
    "NS_ALEX_CTF",
    "/Volumes/NSExternal/ALEXANDRIA/ctf/receipts",
)


def _hash(obj: Dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def emit_receipt(
    event: str,
    subject: str,
    status: str,
    detail: str,
    prev_hash: Optional[str] = None,
    ledger_path: Optional[str] = None,
    ctf_dir: Optional[str] = None,
) -> Dict[str, Any]:
    ts = datetime.now(timezone.utc).isoformat()
    body = {
        "ts": ts,
        "event": event,
        "subject": subject,
        "status": status,
        "detail": detail,
        "prev_hash": prev_hash,
    }
    body["sha256"] = _hash(body)

    lpath = ledger_path or DEFAULT_LEDGER
    cdir = ctf_dir or DEFAULT_CTF

    try:
        Path(lpath).parent.mkdir(parents=True, exist_ok=True)
        with open(lpath, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(body, ensure_ascii=False) + "\n")
    except Exception:
        pass

    try:
        Path(cdir).mkdir(parents=True, exist_ok=True)
        rname = f"{ts.replace(':','-')}-{body['sha256'][:12]}.json"
        with open(os.path.join(cdir, rname), "w", encoding="utf-8") as fh:
            json.dump(body, fh, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return body
