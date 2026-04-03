# Copyright © 2026 Axiolev. All rights reserved.
"""Artifact Writer — standardized path + hash + size + ts for all adapter file outputs."""
from __future__ import annotations
import hashlib, time
from pathlib import Path

ARTIFACTS_ROOT = Path.home() / ".axiolev" / "artifacts"


def write_artifact(run_id: str, op: str, data: bytes | str, suffix: str = ".json") -> dict:
    """Write artifact, return {path, hash, size, ts}."""
    d = ARTIFACTS_ROOT / run_id
    d.mkdir(parents=True, exist_ok=True)
    safe_op = op.replace(".", "_")
    p = d / f"{safe_op}{suffix}"
    if isinstance(data, str):
        data = data.encode()
    p.write_bytes(data)
    h = hashlib.sha256(data).hexdigest()[:16]
    return {
        "path": str(p),
        "hash": h,
        "size": len(data),
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
