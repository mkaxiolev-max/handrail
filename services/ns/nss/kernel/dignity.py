# Copyright © 2026 Axiolev. All rights reserved.
"""
Dignity Kernel — YubiKey Quorum binding.

2-of-3 quorum model (1-of-1 active until 2nd key provisioned):
  slot_1 (primary)   — serial 26116460 — ACTIVE
  slot_2 (backup)    — pending provisioning
  slot_3 (emergency) — pending provisioning

Verify via YubiCloud OTP (api.yubico.com).
All outcomes (pass/fail) written as KernelDecisionReceipts to Alexandria.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Quorum configuration
# ---------------------------------------------------------------------------

YUBIKEY_SERIAL_PRIMARY = "26116460"

QUORUM_SLOTS: dict[str, dict] = {
    "slot_1": {
        "serial":   YUBIKEY_SERIAL_PRIMARY,
        "role":     "primary",
        "active":   True,
        "hw_type":  "YubiKey 5 NFC",
        "algo":     "ECDSA P-256",
    },
    "slot_2": {
        "serial":   None,
        "role":     "backup",
        "active":   False,
    },
    "slot_3": {
        "serial":   None,
        "role":     "emergency",
        "active":   False,
    },
}

# 1-of-active until 2nd key provisioned
QUORUM_THRESHOLD = 1

# ---------------------------------------------------------------------------
# In-memory challenge store  {challenge_id → {nonce, expires_at_ts, used}}
# ---------------------------------------------------------------------------

_CHALLENGES: dict[str, dict] = {}
_CHALLENGE_TTL_S = 300  # 5 minutes

# ---------------------------------------------------------------------------
# Alexandria receipt writer
# ---------------------------------------------------------------------------

_RECEIPT_LOG_SSD      = Path("/Volumes/NSExternal/ALEXANDRIA/ledger/kernel_decisions.jsonl")
_RECEIPT_LOG_FALLBACK = Path.home() / "ALEXANDRIA" / "ledger" / "kernel_decisions.jsonl"

def _receipt_path() -> Path:
    if Path("/Volumes/NSExternal/ALEXANDRIA/ledger").exists():
        return _RECEIPT_LOG_SSD
    p = _RECEIPT_LOG_FALLBACK
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _write_receipt(kind: str, payload: dict) -> str:
    receipt_id = "kdr_" + secrets.token_hex(12)
    entry = {
        "receipt_id": receipt_id,
        "kind":       kind,
        "ts":         datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    try:
        with _receipt_path().open("a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass
    return receipt_id


# ---------------------------------------------------------------------------
# YubikeyQuorum
# ---------------------------------------------------------------------------

class YubikeyQuorum:
    """1-of-1 active quorum (slot_1, serial 26116460). Expands to 2-of-3 when
    slot_2 + slot_3 are provisioned."""

    # ── Challenge generation ────────────────────────────────────────────────

    def generate_challenge(self) -> dict:
        """Generate a one-time 32-byte nonce challenge. TTL=5 minutes."""
        _purge_expired()
        nonce       = secrets.token_hex(32)          # 64 hex chars
        challenge_id = "chk_" + secrets.token_hex(8)
        expires_at_ts = time.time() + _CHALLENGE_TTL_S
        expires_at  = datetime.fromtimestamp(expires_at_ts, tz=timezone.utc).isoformat()

        _CHALLENGES[challenge_id] = {
            "nonce":       nonce,
            "expires_at_ts": expires_at_ts,
            "used":        False,
        }
        return {
            "challenge_id": challenge_id,
            "nonce":        nonce,
            "expires_at":   expires_at,
            "ttl_s":        _CHALLENGE_TTL_S,
            "quorum_required": QUORUM_THRESHOLD,
        }

    # ── OTP verification (synchronous — run in thread from async handlers) ──

    def verify_otp(self, otp: str, challenge_id: str | None = None) -> dict:
        """Verify OTP against YubiCloud. Returns {verified, receipt_id, device_id, error?}."""
        import urllib.request, urllib.parse

        otp = otp.strip()
        modhex = "cbdefghijklnrtuv"

        # Structural validation
        if len(otp) != 44 or not all(c in modhex for c in otp.lower()):
            receipt_id = _write_receipt("VIOLATION", {
                "reason": "invalid_otp_format",
                "otp_len": len(otp),
                "yubikey_verified": False,
            })
            return {"verified": False, "error": "invalid_otp_format", "receipt_id": receipt_id}

        device_id = otp[:12]  # first 12 modhex chars = public identity

        # Challenge expiry / replay check
        if challenge_id:
            ch = _CHALLENGES.get(challenge_id)
            if not ch:
                receipt_id = _write_receipt("VIOLATION", {
                    "reason": "unknown_challenge_id",
                    "challenge_id": challenge_id,
                    "yubikey_verified": False,
                })
                return {"verified": False, "error": "unknown_challenge_id",
                        "receipt_id": receipt_id}
            if time.time() > ch["expires_at_ts"]:
                _CHALLENGES.pop(challenge_id, None)
                receipt_id = _write_receipt("VIOLATION", {
                    "reason": "challenge_expired",
                    "challenge_id": challenge_id,
                    "yubikey_verified": False,
                })
                return {"verified": False, "error": "challenge_expired",
                        "receipt_id": receipt_id}
            if ch["used"]:
                receipt_id = _write_receipt("VIOLATION", {
                    "reason": "challenge_already_used",
                    "challenge_id": challenge_id,
                    "yubikey_verified": False,
                })
                return {"verified": False, "error": "challenge_replay_denied",
                        "receipt_id": receipt_id}

        # YubiCloud verification
        client_id = os.environ.get("YUBIKEY_CLIENT_ID", "").strip() or "1"
        nonce     = secrets.token_hex(16)
        params    = urllib.parse.urlencode({"id": client_id, "otp": otp, "nonce": nonce})
        url       = f"https://api.yubico.com/wsapi/2.0/verify?{params}"

        cloud_status = "UNKNOWN"
        try:
            with urllib.request.urlopen(url, timeout=8) as resp:
                body = resp.read().decode()
            result: dict = {}
            for line in body.strip().splitlines():
                if "=" in line:
                    k, _, v = line.partition("=")
                    result[k.strip()] = v.strip()
            cloud_status = result.get("status", "UNKNOWN")
        except Exception as e:
            cloud_status = f"NETWORK_ERROR:{str(e)[:60]}"

        verified = cloud_status == "OK"

        if challenge_id and verified:
            _CHALLENGES[challenge_id]["used"] = True

        receipt_id = _write_receipt(
            "YUBIKEY_VERIFY_OK" if verified else "YUBIKEY_VERIFY_FAIL",
            {
                "device_id":      device_id,
                "serial":         YUBIKEY_SERIAL_PRIMARY,
                "challenge_id":   challenge_id,
                "cloud_status":   cloud_status,
                "yubikey_verified": verified,
                "quorum_slots_active": 1,
                "quorum_threshold":    QUORUM_THRESHOLD,
            },
        )

        if not verified:
            return {
                "verified": False,
                "error":    f"otp_rejected:{cloud_status}",
                "receipt_id": receipt_id,
                "device_id": device_id,
            }

        return {
            "verified":        True,
            "receipt_id":      receipt_id,
            "device_id":       device_id,
            "serial":          YUBIKEY_SERIAL_PRIMARY,
            "cloud_status":    cloud_status,
            "yubikey_verified": True,
            "quorum_satisfied": True,
        }

    # ── Quorum status ───────────────────────────────────────────────────────

    def status(self, last_verified_at: str | None = None) -> dict:
        active_slots = sum(1 for s in QUORUM_SLOTS.values() if s["active"])
        return {
            "serial":          YUBIKEY_SERIAL_PRIMARY,
            "quorum_threshold": QUORUM_THRESHOLD,
            "quorum_slots":    {
                k: {"role": v["role"], "active": v["active"], "serial": v.get("serial")}
                for k, v in QUORUM_SLOTS.items()
            },
            "active_slots":    active_slots,
            "quorum_satisfied": active_slots >= QUORUM_THRESHOLD,
            "verified_at":     last_verified_at,
            "client_id_set":   bool(os.environ.get("YUBIKEY_CLIENT_ID", "").strip()),
            "mode":            "live_yubicloud" if os.environ.get("YUBIKEY_CLIENT_ID") else "demo_client_1",
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _purge_expired() -> None:
    now = time.time()
    expired = [k for k, v in _CHALLENGES.items() if now > v["expires_at_ts"]]
    for k in expired:
        _CHALLENGES.pop(k, None)


# Module-level singleton
_quorum: YubikeyQuorum | None = None

def get_quorum() -> YubikeyQuorum:
    global _quorum
    if _quorum is None:
        _quorum = YubikeyQuorum()
    return _quorum
