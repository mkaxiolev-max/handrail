# Copyright © 2026 Axiolev. All rights reserved.
"""
SAN State — Sovereign Authority Node legal-reality layer.
Tracks LLC, EIN, Stripe, YubiKey quorum, equity table status.
All updates are append-only audited to Alexandria.
"""
from __future__ import annotations
import json
import time
from pathlib import Path

_AUDIT_SSD      = Path("/Volumes/NSExternal/ALEXANDRIA/san_audit.jsonl")
_AUDIT_FALLBACK = Path.home() / ".axiolev" / "san_audit.jsonl"
_STATE_SSD      = Path("/Volumes/NSExternal/ALEXANDRIA/san_state.json")
_STATE_FALLBACK = Path.home() / ".axiolev" / "san_state.json"

_SEED_STATE: dict = {
    "llc_active":        True,
    "ein":               None,
    "stripe_verified":   False,
    "yubikey_slot1":     True,
    "yubikey_slot2":     False,
    "equity_table_hash": None,
    "ip_filings":        [],
    "notes":             "LLC formed; EIN pending IRS issuance; Stripe business verification pending",
}

VALID_FIELDS = set(_SEED_STATE.keys())


def _ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _state_path() -> Path:
    if Path("/Volumes/NSExternal/ALEXANDRIA").exists():
        return _STATE_SSD
    p = _STATE_FALLBACK
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _audit_path() -> Path:
    if Path("/Volumes/NSExternal/ALEXANDRIA").exists():
        return _AUDIT_SSD
    p = _AUDIT_FALLBACK
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def get_state() -> dict:
    p = _state_path()
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    state = {**_SEED_STATE, "updated_at": _ts()}
    p.write_text(json.dumps(state, indent=2))
    return state


def update(field: str, value) -> dict:
    if field not in VALID_FIELDS:
        return {"ok": False, "error": f"unknown field: {field}"}
    state = get_state()
    old_value = state.get(field)
    state[field] = value
    state["updated_at"] = _ts()
    _state_path().write_text(json.dumps(state, indent=2))
    entry = {
        "ts": _ts(),
        "field": field,
        "old": old_value,
        "new": value,
    }
    try:
        ap = _audit_path()
        ap.parent.mkdir(parents=True, exist_ok=True)
        with ap.open("a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass
    return {"ok": True, "field": field, "value": value, "ts": state["updated_at"]}


def can_execute_financial_ops() -> bool:
    state = get_state()
    return bool(state.get("llc_active") and state.get("stripe_verified"))


def san_summary() -> dict:
    state = get_state()
    blockers = []
    if not state.get("llc_active"):
        blockers.append("LLC not active")
    if not state.get("ein"):
        blockers.append("EIN not yet issued")
    if not state.get("stripe_verified"):
        blockers.append("Stripe business verification pending")
    if not state.get("yubikey_slot2"):
        blockers.append("YubiKey slot 2 not enrolled (2-of-3 quorum incomplete)")
    return {
        "state": state,
        "can_execute_financial_ops": can_execute_financial_ops(),
        "blockers": blockers,
        "blocker_count": len(blockers),
        "ts": _ts(),
    }
