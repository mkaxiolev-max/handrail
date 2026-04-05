# Copyright © 2026 Axiolev. All rights reserved.
"""
YubiKey 2-of-3 Sovereign Quorum Module
=======================================
Implements a slot registry, HMAC-signed session tokens, and quorum verification
for the Handrail boot.runtime policy gate.

Physical YubiKey OTP verification is handled by NS /kernel/yubikey/verify.
This module governs the *quorum* layer: which slots are enrolled, whether a
presented session token is fresh and valid, and whether the required threshold
of slots satisfies sovereign boot.

Design
------
- QuorumSlot: slot_id + serial + enrolled_at + public_key_hash
- QuorumStore: reads/writes WORKSPACE/.yubikey/quorum.json
- Tokens: ysk_<32 hex> — HMAC-SHA256(key=NS_FOUNDER_PASSWORD, msg=slot_id:timestamp)
  — 5-minute TTL, tracked in an in-process TOKEN_STORE dict
  — format matches existing server.py _YSK_TOKEN_RE regex
- verify_quorum(token, required_slots=1) — token auth + enrolled-slot count check
- 2-of-3 ready: quorum_threshold in quorum.json; raise it to 2 when slot_2 arrives
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

_log = logging.getLogger("handrail.yubikey_quorum")

# ── Constants ─────────────────────────────────────────────────────────────────

TOKEN_TTL_SECONDS = 300          # 5-minute session token lifetime
_TOKEN_RE = re.compile(r"^ysk_[0-9a-f]{32}$")

# In-process token store: token → {"slot_id": str, "issued_at": float}
# Cleared on server restart (intentional — tokens are short-lived).
TOKEN_STORE: Dict[str, dict] = {}

# Signing secret — falls back to "handrail-quorum-dev" if env not set
def _signing_secret() -> bytes:
    return os.environ.get("NS_FOUNDER_PASSWORD", "handrail-quorum-dev").encode()


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class QuorumSlot:
    slot_id: str           # "slot_1" | "slot_2" | "slot_3"
    serial: str            # YubiKey hardware serial number
    enrolled_at: str       # ISO-8601 timestamp
    public_key_hash: str   # HMAC-SHA256(secret, serial:slot_id)[:16]


@dataclass
class QuorumResult:
    ok: bool
    slots_verified: int    # enrolled slots that satisfy threshold
    sovereign: bool        # slots_verified >= required threshold
    reason: str = ""


# ── Quorum store ──────────────────────────────────────────────────────────────

def _registry_path() -> Path:
    workspace = Path(os.environ.get("HR_WORKSPACE", "/app"))
    return workspace / ".yubikey" / "quorum.json"


class QuorumStore:
    """Reads and writes the slot registry from WORKSPACE/.yubikey/quorum.json."""

    @staticmethod
    def load() -> dict:
        p = _registry_path()
        if not p.exists():
            return {"quorum_threshold": 1, "slots": {}}
        try:
            return json.loads(p.read_text())
        except Exception as e:
            _log.warning("QuorumStore.load failed: %s", e)
            return {"quorum_threshold": 1, "slots": {}}

    @staticmethod
    def save(registry: dict) -> None:
        p = _registry_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(registry, indent=2))

    @staticmethod
    def enroll_slot(slot_id: str, serial: str, public_key_hash: str) -> QuorumSlot:
        """Add or update a slot in the registry. Returns the enrolled QuorumSlot."""
        registry = QuorumStore.load()
        enrolled_at = datetime.now(timezone.utc).isoformat()
        slot = QuorumSlot(
            slot_id=slot_id,
            serial=serial,
            enrolled_at=enrolled_at,
            public_key_hash=public_key_hash,
        )
        registry["slots"][slot_id] = asdict(slot)
        QuorumStore.save(registry)
        _log.info("QuorumStore: enrolled %s serial=%s", slot_id, serial)
        return slot

    @staticmethod
    def get_slots() -> List[QuorumSlot]:
        registry = QuorumStore.load()
        slots = []
        for raw in registry.get("slots", {}).values():
            try:
                slots.append(QuorumSlot(**raw))
            except Exception:
                pass
        return slots

    @staticmethod
    def get_threshold() -> int:
        return int(QuorumStore.load().get("quorum_threshold", 1))


# ── Token generation and verification ─────────────────────────────────────────

def generate_session_token(slot_id: str) -> str:
    """
    Generate a signed session token for a given slot_id.

    Token format: ysk_<32 lowercase hex chars>
    Signing:      HMAC-SHA256(NS_FOUNDER_PASSWORD, "{slot_id}:{unix_ts_int}")[:32]
    Side effect:  token is stored in TOKEN_STORE with issued_at for TTL checks.
    """
    ts = int(time.time())
    msg = f"{slot_id}:{ts}".encode()
    sig = hmac.new(_signing_secret(), msg, hashlib.sha256).hexdigest()[:32]
    token = f"ysk_{sig}"
    TOKEN_STORE[token] = {"slot_id": slot_id, "issued_at": ts}
    _log.info("generate_session_token: issued token for %s (ts=%s)", slot_id, ts)
    return token


def verify_session_token(token: str) -> dict:
    """
    Validate a session token.

    Returns: {ok: bool, slot_id: str|None, reason: str, age_seconds: int|None}
    Checks:  format regex, presence in TOKEN_STORE, 5-minute TTL.
    """
    if not token or not _TOKEN_RE.match(token):
        return {"ok": False, "slot_id": None, "reason": "invalid_token_format", "age_seconds": None}

    entry = TOKEN_STORE.get(token)
    if entry is None:
        return {"ok": False, "slot_id": None, "reason": "token_not_found_or_expired_on_restart", "age_seconds": None}

    age = int(time.time()) - entry["issued_at"]
    if age > TOKEN_TTL_SECONDS:
        del TOKEN_STORE[token]
        return {"ok": False, "slot_id": entry["slot_id"], "reason": "token_expired", "age_seconds": age}

    return {"ok": True, "slot_id": entry["slot_id"], "reason": "ok", "age_seconds": age}


# ── Quorum verification ────────────────────────────────────────────────────────

def verify_quorum(token: str, required_slots: int = 1) -> QuorumResult:
    """
    Verify a session token against the enrolled slot registry.

    Steps:
    1. Validate token (format + TTL)
    2. Confirm the token's slot_id is in the enrolled registry
    3. Count enrolled slots and compare to required_slots threshold
    4. Return QuorumResult(ok, slots_verified, sovereign)

    sovereign=True only when slots_verified >= required_slots.
    """
    tok = verify_session_token(token)
    if not tok["ok"]:
        return QuorumResult(ok=False, slots_verified=0, sovereign=False, reason=tok["reason"])

    slot_id = tok["slot_id"]
    slots = QuorumStore.get_slots()
    enrolled_ids = {s.slot_id for s in slots}

    if slot_id not in enrolled_ids:
        return QuorumResult(
            ok=False, slots_verified=0, sovereign=False,
            reason=f"slot_not_enrolled: {slot_id}"
        )

    enrolled_count = len(enrolled_ids)
    sovereign = enrolled_count >= required_slots

    return QuorumResult(
        ok=True,
        slots_verified=enrolled_count,
        sovereign=sovereign,
        reason="quorum_satisfied" if sovereign else f"quorum_insufficient: {enrolled_count}/{required_slots}",
    )


# ── Status ────────────────────────────────────────────────────────────────────

def get_quorum_status() -> dict:
    """
    Return the full quorum status for GET /yubikey/status.

    Fields:
      enrolled_count   — number of enrolled slots
      quorum_threshold — required for sovereign (from quorum.json)
      quorum_ready     — enrolled_count >= quorum_threshold
      sovereign        — alias for quorum_ready
      slots            — list of enrolled slot summaries (no secrets)
      active_tokens    — count of in-process live tokens (debug)
    """
    slots = QuorumStore.get_slots()
    threshold = QuorumStore.get_threshold()
    enrolled_count = len(slots)
    quorum_ready = enrolled_count >= threshold

    now = time.time()
    live_tokens = sum(
        1 for v in TOKEN_STORE.values()
        if (now - v["issued_at"]) <= TOKEN_TTL_SECONDS
    )

    return {
        "enrolled_count":   enrolled_count,
        "quorum_threshold": threshold,
        "quorum_ready":     quorum_ready,
        "sovereign":        quorum_ready,
        "slots": [
            {
                "slot_id":        s.slot_id,
                "serial":         s.serial,
                "enrolled_at":    s.enrolled_at,
                "public_key_hash": s.public_key_hash,
            }
            for s in slots
        ],
        "active_tokens": live_tokens,
    }


# ── Convenience: compute public_key_hash for a new slot ───────────────────────

def compute_public_key_hash(serial: str, slot_id: str) -> str:
    """HMAC-SHA256(signing_secret, '{serial}:{slot_id}')[:16] — canonical slot fingerprint."""
    msg = f"{serial}:{slot_id}".encode()
    return hmac.new(_signing_secret(), msg, hashlib.sha256).hexdigest()[:16]
