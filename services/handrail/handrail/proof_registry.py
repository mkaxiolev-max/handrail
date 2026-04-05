# Copyright © 2026 Axiolev. All rights reserved.
"""
Universal Proof Registry
========================
One truth surface for all constitutional state transitions in NS∞.

Every sovereign action emits a ProofEntry into the append-only ledger at
WORKSPACE/.run/proof_registry.jsonl.  The registry is the canonical source
of truth for: which boot receipts exist, which schemas are frozen, which
YubiKey slots are enrolled, and all future governance events.

Proof types
-----------
BOOT                  BootProofReceipt emitted after boot_mission_graph
SCHEMA_FREEZE         Frozen ABI schema fingerprint recorded at startup
QUORUM_ENROLLMENT     YubiKey slot enrolled via POST /yubikey/enroll
CAPABILITY_PROMOTION  Capability state transition (desired→canonical)
POLICY_CHANGE         Policy profile modified
FOUNDER_APPROVAL      Explicit founder sign-off on a governance action
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import string
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

_log = logging.getLogger("handrail.proof_registry")


# ── Proof type enum ────────────────────────────────────────────────────────────

class ProofType(str, Enum):
    BOOT                 = "BOOT"
    SCHEMA_FREEZE        = "SCHEMA_FREEZE"
    QUORUM_ENROLLMENT    = "QUORUM_ENROLLMENT"
    CAPABILITY_PROMOTION = "CAPABILITY_PROMOTION"
    POLICY_CHANGE        = "POLICY_CHANGE"
    FOUNDER_APPROVAL     = "FOUNDER_APPROVAL"

VALID_PROOF_TYPES = {t.value for t in ProofType}


# ── ProofEntry dataclass ───────────────────────────────────────────────────────

@dataclass
class ProofEntry:
    proof_id:   str               # PRF-XXXXXXXX
    proof_type: str               # ProofType value
    sovereign:  bool              # true if this entry reflects a sovereign state
    timestamp:  str               # ISO-8601 UTC
    hash:       str               # fingerprint relevant to this proof type
    metadata:   Dict = field(default_factory=dict)


def _make_proof_id() -> str:
    chars = string.ascii_uppercase + string.digits
    return "PRF-" + "".join(random.choices(chars, k=8))


# ── Registry store ─────────────────────────────────────────────────────────────

def _registry_path() -> Path:
    workspace = Path(os.environ.get("HR_WORKSPACE", "/app"))
    return workspace / ".run" / "proof_registry.jsonl"


def _boot_receipts_path() -> Optional[Path]:
    """Returns the path of the boot_receipts.jsonl that exists, or None."""
    for p in (
        Path("/Volumes/NSExternal/.run/boot_receipts.jsonl"),
        Path(os.environ.get("HR_WORKSPACE", "/app")) / ".runs" / "boot_receipts.jsonl",
    ):
        if p.exists():
            return p
    return None


class ProofRegistry:
    """
    Append-only proof ledger backed by WORKSPACE/.run/proof_registry.jsonl.

    All writes are atomic line-appends (jsonl). Reads scan the full file.
    """

    # ── Write ──────────────────────────────────────────────────────────────────

    @staticmethod
    def append(entry: ProofEntry) -> ProofEntry:
        """Append a ProofEntry to the ledger. Returns the entry."""
        path = _registry_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a") as f:
                f.write(json.dumps(asdict(entry)) + "\n")
        except Exception as e:
            _log.warning("ProofRegistry.append failed: %s", e)
        return entry

    @staticmethod
    def _read_all() -> List[Dict]:
        path = _registry_path()
        if not path.exists():
            return []
        try:
            lines = [l.strip() for l in path.read_text().splitlines() if l.strip()]
            return [json.loads(l) for l in lines]
        except Exception as e:
            _log.warning("ProofRegistry._read_all failed: %s", e)
            return []

    # ── Read ───────────────────────────────────────────────────────────────────

    @staticmethod
    def latest(proof_type: str) -> Optional[Dict]:
        """Return the most recent entry of the given proof_type, or None."""
        entries = [e for e in ProofRegistry._read_all() if e.get("proof_type") == proof_type]
        return entries[-1] if entries else None

    @staticmethod
    def history(proof_type: str, n: int = 10) -> List[Dict]:
        """Return the last n entries of the given proof_type, newest-last."""
        entries = [e for e in ProofRegistry._read_all() if e.get("proof_type") == proof_type]
        return entries[-n:]

    @staticmethod
    def full_chain() -> List[Dict]:
        """Return all entries ordered by timestamp, newest-first."""
        entries = ProofRegistry._read_all()
        try:
            entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        except Exception:
            pass
        return entries

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def types_present() -> List[str]:
        return sorted({e.get("proof_type") for e in ProofRegistry._read_all() if e.get("proof_type")})

    @staticmethod
    def entry_count() -> int:
        return len(ProofRegistry._read_all())

    # ── Factory helpers ────────────────────────────────────────────────────────

    @staticmethod
    def make_boot_entry(receipt: Dict) -> ProofEntry:
        return ProofEntry(
            proof_id=_make_proof_id(),
            proof_type=ProofType.BOOT.value,
            sovereign=bool(receipt.get("sovereign")),
            timestamp=receipt.get("timestamp", datetime.now(timezone.utc).isoformat()),
            hash=receipt.get("all_phases_hash", ""),
            metadata={
                "receipt_id": receipt.get("receipt_id"),
                "boot_id":    receipt.get("boot_id"),
                "boot_mode":  receipt.get("boot_mode"),
            },
        )

    @staticmethod
    def make_schema_freeze_entry(schema_name: str, freeze_hash: str) -> ProofEntry:
        return ProofEntry(
            proof_id=_make_proof_id(),
            proof_type=ProofType.SCHEMA_FREEZE.value,
            sovereign=True,
            timestamp=datetime.now(timezone.utc).isoformat(),
            hash=freeze_hash,
            metadata={"schema_name": schema_name},
        )

    @staticmethod
    def make_quorum_enrollment_entry(slot_id: str, serial: str, pkh: str) -> ProofEntry:
        combined = hashlib.sha256(f"{slot_id}:{serial}:{pkh}".encode()).hexdigest()[:16]
        return ProofEntry(
            proof_id=_make_proof_id(),
            proof_type=ProofType.QUORUM_ENROLLMENT.value,
            sovereign=True,
            timestamp=datetime.now(timezone.utc).isoformat(),
            hash=combined,
            metadata={"slot_id": slot_id, "serial": serial, "public_key_hash": pkh},
        )


# ── Startup seeding ────────────────────────────────────────────────────────────

def startup_seed(abi_freeze_manifest: Dict[str, str]) -> None:
    """
    Called once at server startup.

    1. Backfill BOOT entries from existing boot_receipts.jsonl (idempotent —
       skips entries whose receipt_id is already in the registry).
    2. Seed SCHEMA_FREEZE entries if none exist yet (idempotent).
    """
    existing = ProofRegistry._read_all()

    # ── 1. Backfill BOOT entries ───────────────────────────────────────────────
    known_receipt_ids = {
        e.get("metadata", {}).get("receipt_id")
        for e in existing
        if e.get("proof_type") == ProofType.BOOT.value
    }
    br_path = _boot_receipts_path()
    if br_path:
        try:
            for line in br_path.read_text().splitlines():
                line = line.strip()
                if not line:
                    continue
                receipt = json.loads(line)
                if receipt.get("receipt_id") not in known_receipt_ids:
                    entry = ProofRegistry.make_boot_entry(receipt)
                    ProofRegistry.append(entry)
                    known_receipt_ids.add(receipt.get("receipt_id"))
                    _log.info("startup_seed: backfilled BOOT %s", receipt.get("receipt_id"))
        except Exception as e:
            _log.warning("startup_seed: BOOT backfill failed: %s", e)

    # ── 2. Seed SCHEMA_FREEZE entries ─────────────────────────────────────────
    existing_frozen = {
        e.get("metadata", {}).get("schema_name")
        for e in ProofRegistry._read_all()
        if e.get("proof_type") == ProofType.SCHEMA_FREEZE.value
    }
    for schema_name, freeze_hash in abi_freeze_manifest.items():
        if schema_name not in existing_frozen:
            entry = ProofRegistry.make_schema_freeze_entry(schema_name, freeze_hash)
            ProofRegistry.append(entry)
            _log.info("startup_seed: seeded SCHEMA_FREEZE %s @ %s", schema_name, freeze_hash)
