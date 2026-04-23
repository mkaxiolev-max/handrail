"""NVIR Dispatcher — domain-tag router + VerificationReceipt emitter.
© 2026 AXIOLEV Holdings LLC

Routes claims by domain tag to the correct oracle, then emits a
VerificationReceipt to the Lineage Fabric ledger at ledger/nvir/.

Receipt chain:  each receipt SHA256-hashes the previous receipt's hash,
forming a Byzantine-resistant append-only audit ledger matching the pattern
used by services/ns/nss/core/receipts.py.

Ledger paths (primary / fallback):
  /Volumes/NSExternal/ALEXANDRIA/ledger/nvir/verification_receipts.jsonl
  ~/.axiolev/ALEXANDRIA/ledger/nvir/verification_receipts.jsonl
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Optional, Union

from .generator import GeneratedCandidate
from .oracle import MathLeanOracle, LogicSMTOracle, CodeUnitOracle, OracleVerdict


# ── paths ─────────────────────────────────────────────────────────────────────

_ALEX_ROOT = pathlib.Path(
    os.environ.get("ALEXANDRIA", "/Volumes/NSExternal/ALEXANDRIA")
)
_FALLBACK = pathlib.Path(os.path.expanduser("~/.axiolev/ALEXANDRIA"))


def _ledger_dir() -> pathlib.Path:
    base = _ALEX_ROOT if _ALEX_ROOT.exists() else _FALLBACK
    d = base / "ledger" / "nvir"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _ledger_path() -> pathlib.Path:
    return _ledger_dir() / "verification_receipts.jsonl"


# ── receipt ───────────────────────────────────────────────────────────────────

@dataclass
class VerificationReceipt:
    receipt_id: str
    generation_id: str      # links to GeneratedCandidate.generation_id
    domain: str
    claim_hash: str         # sha256[:16] of claim text
    oracle: str             # "math_lean" | "logic_smt" | "code_unit" | "general"
    verdict: bool
    confidence: float
    oracle_method: str
    oracle_detail: dict
    ts_utc: str
    prev_hash: str          # sha256 of previous receipt (or "genesis")
    receipt_hash: str       # sha256 of this receipt (all fields above)

    def to_dict(self) -> dict:
        return asdict(self)


def _sha256(s: str) -> str:
    return "sha256:" + hashlib.sha256(s.encode()).hexdigest()


def _receipt_hash(r: dict) -> str:
    """Hash a receipt dict excluding the receipt_hash field."""
    payload = {k: v for k, v in r.items() if k != "receipt_hash"}
    return _sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")))


# ── receipt chain ─────────────────────────────────────────────────────────────

_CHAIN_LOCK = threading.Lock()
_COUNTER = 0
_PREV_HASH = "genesis"


def _next_receipt_id() -> str:
    global _COUNTER
    _COUNTER += 1
    return f"NVIR_R_{_COUNTER:06d}"


def _emit_receipt(
    generation_id: str,
    domain: str,
    claim: str,
    oracle_name: str,
    verdict: OracleVerdict,
    ledger: Optional[pathlib.Path] = None,
) -> VerificationReceipt:
    """Build and append a VerificationReceipt to the ledger."""
    global _PREV_HASH, _COUNTER

    with _CHAIN_LOCK:
        # Read last hash from ledger if counter is 0 (fresh process)
        if _COUNTER == 0:
            lp = ledger or _ledger_path()
            if lp.is_file():
                try:
                    last_line = lp.read_text().splitlines()[-1]
                    last = json.loads(last_line)
                    _PREV_HASH = last.get("receipt_hash", "genesis")
                    # parse counter from last receipt_id
                    rid = last.get("receipt_id", "NVIR_R_000000")
                    try:
                        _COUNTER = int(rid.split("_")[-1])
                    except (ValueError, IndexError):
                        _COUNTER = 0
                except Exception:
                    pass

        _COUNTER += 1
        rid = f"NVIR_R_{_COUNTER:06d}"
        prev = _PREV_HASH

        proto = {
            "receipt_id": rid,
            "generation_id": generation_id,
            "domain": domain,
            "claim_hash": hashlib.sha256(claim.encode()).hexdigest()[:16],
            "oracle": oracle_name,
            "verdict": verdict.valid,
            "confidence": verdict.confidence,
            "oracle_method": verdict.method,
            "oracle_detail": verdict.detail,
            "ts_utc": _utc_now(),
            "prev_hash": prev,
            "receipt_hash": "",
        }
        proto["receipt_hash"] = _receipt_hash(proto)
        _PREV_HASH = proto["receipt_hash"]

        receipt = VerificationReceipt(**proto)

        # Append to ledger (best-effort)
        try:
            lp = ledger or _ledger_path()
            with lp.open("a", encoding="utf-8") as f:
                f.write(json.dumps(proto, separators=(",", ":")) + "\n")
        except OSError:
            pass

    return receipt


# ── domain oracle registry ────────────────────────────────────────────────────

_ORACLE_REGISTRY: dict[str, tuple[object, str]] = {}  # domain → (oracle, name)
_REGISTRY_LOCK = threading.Lock()


def _get_or_build_oracle(domain: str) -> tuple[object, str]:
    with _REGISTRY_LOCK:
        if domain not in _ORACLE_REGISTRY:
            if domain == "math":
                _ORACLE_REGISTRY[domain] = (MathLeanOracle(), "math_lean")
            elif domain == "logic":
                _ORACLE_REGISTRY[domain] = (LogicSMTOracle(), "logic_smt")
            elif domain == "code":
                _ORACLE_REGISTRY[domain] = (CodeUnitOracle(), "code_unit")
            else:
                _ORACLE_REGISTRY[domain] = (_GeneralOracle(), "general")
    return _ORACLE_REGISTRY[domain]


class _GeneralOracle:
    """General-purpose oracle: JSON with ≥2 keys + length ≥10 (matches live_loop semantics)."""

    def validate(self, claim: str) -> OracleVerdict:
        import json as _json  # noqa: PLC0415
        try:
            d = _json.loads(claim)
            valid = isinstance(d, dict) and len(d) >= 2 and len(claim) >= 10
        except (_json.JSONDecodeError, ValueError):
            valid = len(claim.strip()) >= 10
        return OracleVerdict(
            valid=valid, confidence=0.85,
            method="general_structural",
            detail={"length": len(claim)},
        )

    def __call__(self, claim: str) -> bool:
        return self.validate(claim).valid


# ── dispatcher ────────────────────────────────────────────────────────────────

class NVIRDispatcher:
    """Routes claims to domain-specific oracles and emits VerificationReceipts.

    Usage::

        dispatcher = NVIRDispatcher()
        receipt = dispatcher.verify(candidate)          # GeneratedCandidate
        receipt2 = dispatcher.verify_raw("2+2=4", "math", "gen_001")
    """

    def __init__(self, ledger: Optional[pathlib.Path] = None):
        self._ledger = ledger

    def verify(self, candidate: GeneratedCandidate) -> VerificationReceipt:
        """Verify a GeneratedCandidate; oracle chosen by candidate.domain."""
        return self.verify_raw(
            claim=candidate.content,
            domain=candidate.domain,
            generation_id=candidate.generation_id,
        )

    def verify_raw(
        self,
        claim: str,
        domain: str,
        generation_id: Optional[str] = None,
    ) -> VerificationReceipt:
        """Verify an arbitrary claim string with a given domain tag."""
        oracle, oracle_name = _get_or_build_oracle(domain)
        verdict: OracleVerdict = oracle.validate(claim)
        return _emit_receipt(
            generation_id=generation_id or str(uuid.uuid4()),
            domain=domain,
            claim=claim,
            oracle_name=oracle_name,
            verdict=verdict,
            ledger=self._ledger,
        )

    def verify_batch(
        self, candidates: list[GeneratedCandidate]
    ) -> list[VerificationReceipt]:
        return [self.verify(c) for c in candidates]

    @staticmethod
    def verify_chain(ledger: Optional[pathlib.Path] = None) -> dict:
        """Verify the integrity of the receipt chain. Returns summary dict."""
        lp = ledger or _ledger_path()
        if not lp.is_file():
            return {"status": "empty", "n_receipts": 0, "broken_at": None}
        lines = lp.read_text().splitlines()
        prev = "genesis"
        for i, line in enumerate(lines):
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                return {"status": "corrupted", "n_receipts": i, "broken_at": i}
            if r.get("prev_hash") != prev:
                return {"status": "broken", "n_receipts": len(lines), "broken_at": i}
            expected = _receipt_hash(r)
            if r.get("receipt_hash") != expected:
                return {"status": "tampered", "n_receipts": len(lines), "broken_at": i}
            prev = r["receipt_hash"]
        return {"status": "ok", "n_receipts": len(lines), "broken_at": None}


# ── utility ───────────────────────────────────────────────────────────────────

def _utc_now() -> str:
    import datetime  # noqa: PLC0415
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
