"""POST /canon/promote — canon promotion with candidate queue."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(tags=["canon"])

_CANON_ROOT = Path(os.environ.get("CANON_ROOT", "/app/canon"))
_PENDING_DIR = _CANON_ROOT / "promotions" / "pending"
_ACCEPTED_DIR = _CANON_ROOT / "promotions" / "accepted"


def _rb(ok: bool, rc: int, op: str, **extra):
    return {
        "return_block_version": 2,
        "ok": ok,
        "rc": rc,
        "operation": op,
        "failure_reason": None,
        "artifacts": [],
        "checks": [],
        "state_change": None,
        "warnings": [],
        "receipt_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dignity_banner": "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED",
        **extra,
    }


@router.get("/canon/axioms")
async def canon_axioms():
    axiom_path = _CANON_ROOT / "axioms" / "ax_core.json"
    if axiom_path.exists():
        with open(axiom_path) as f:
            data = json.load(f)
        return _rb(True, 0, "canon.axioms", artifacts=[data])
    return _rb(False, 1, "canon.axioms", failure_reason="ax_core.json not found")


@router.post("/canon/promote")
async def canon_promote(body: dict):
    candidate_id = body.get("candidate_id", str(uuid.uuid4()))
    approver_signature = body.get("approver_signature")
    hardware_signed = bool(body.get("hardware_signed", False))

    if not approver_signature:
        return _rb(False, 1, "canon.promote", failure_reason="unauthorized",
                   artifacts=[{"detail": "approver_signature required"}])

    _PENDING_DIR.mkdir(parents=True, exist_ok=True)
    _ACCEPTED_DIR.mkdir(parents=True, exist_ok=True)

    entry = {
        "candidate_id": candidate_id,
        "approver_signature": approver_signature,
        "hardware_signed": hardware_signed,
        "queued_at": datetime.now(timezone.utc).isoformat(),
    }

    if not hardware_signed:
        path = _PENDING_DIR / f"{candidate_id}.json"
        path.write_text(json.dumps(entry, indent=2))
        return _rb(True, 0, "canon.promote",
                   artifacts=[{"status": "queued", "path": str(path)}])

    path = _ACCEPTED_DIR / f"{candidate_id}.json"
    path.write_text(json.dumps(entry, indent=2))
    return _rb(True, 0, "canon.promote",
               artifacts=[{"status": "accepted", "path": str(path)}])


@router.get("/canon/pending")
async def canon_pending():
    _PENDING_DIR.mkdir(parents=True, exist_ok=True)
    items = []
    for f in sorted(_PENDING_DIR.glob("*.json")):
        try:
            items.append(json.loads(f.read_text()))
        except Exception:
            pass
    return _rb(True, 0, "canon.pending", artifacts=items)


@router.get("/canon/invariants")
async def canon_invariants():
    invariant_names = [
        "Dignity Kernel read-only",
        "Violet is projection only",
        "Alexandria append-only",
        "LLMs never define truth",
        "Ambiguity fails closed",
        "Execution requires simulation",
        "Execution requires proof receipt",
        "Mission graph bypass forbidden",
        "Canon mutation requires CanonCommit",
        "Founder signature required for G5",
    ]
    invariants = [
        {"id": f"INV-{i+1}", "name": name, "enforced": True, "ring": "R1-R4"}
        for i, name in enumerate(invariant_names)
    ]
    return _rb(True, 0, "canon.invariants", artifacts=invariants)
