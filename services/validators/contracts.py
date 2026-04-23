"""Validator adapter contracts — AXIOLEV Holdings LLC © 2026.

Ontology: lineage via Lineage Fabric; storage via Alexandrian Archive.
I3 constraint: admin ceiling 95.0 — no adapter may return confidence > I3_ADMIN_CAP.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal, Optional, Protocol, runtime_checkable

Verdict = Literal["PASS", "FAIL", "UNCERTAIN", "UNSUPPORTED"]

I3_ADMIN_CAP: float = 0.95  # I3 external admin ceiling — hard limit across all adapters


@dataclass(frozen=True)
class ValidationResult:
    """Shared result schema for every ValidatorAdapter.

    Invariants (enforced in __post_init__):
      - receipt_id / lineage_hash are non-null (Lineage Fabric anchor)
      - confidence ∈ [0.0, I3_ADMIN_CAP]
    """

    claim_id: str
    domain: str
    adapter: str
    verdict: Verdict
    confidence: float           # 0.0–I3_ADMIN_CAP; cap enforced by cap_confidence()
    rationale: str
    checks: Dict[str, Any]
    flags: List[str]            # warnings, policy notes, regulatory flags
    audit_trail: List[Dict[str, Any]]  # append-only audit entries (FDA / compliance)
    receipt_id: str             # Lineage Fabric receipt — non-null
    lineage_hash: str           # SHA-256 chain hash — non-null
    ts: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if not self.receipt_id or not self.lineage_hash:
            raise ValueError(
                f"ValidationResult from {self.adapter!r} must carry non-null "
                "receipt_id and lineage_hash (Lineage Fabric anchors required)"
            )
        if not (0.0 <= self.confidence <= I3_ADMIN_CAP):
            raise ValueError(
                f"confidence {self.confidence} violates I3.admin cap "
                f"[0.0, {I3_ADMIN_CAP}] for adapter {self.adapter!r}"
            )

    def to_json(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"))

    @property
    def result_digest(self) -> str:
        """SHA-256 of this result's canonical JSON (Lineage proof point)."""
        return "sha256:" + hashlib.sha256(self.to_json().encode()).hexdigest()


@runtime_checkable
class ValidatorAdapter(Protocol):
    """Structural protocol every domain adapter must satisfy.

    Conformance verified at registration time via isinstance() against this
    @runtime_checkable Protocol.
    """

    domain: str

    def validate(self, claim: Dict[str, Any], context: Dict[str, Any]) -> ValidationResult:
        """Validate *claim* against domain rules.

        Args:
            claim:   Domain-specific claim dict.
            context: Caller context — actor, session_id, policy flags, etc.

        Returns:
            A frozen ValidationResult anchored to the Lineage Fabric.
        """
        ...


# ---------------------------------------------------------------------------
# Lineage Fabric — lightweight in-process chained receipt store
# ---------------------------------------------------------------------------

_LINEAGE_STATE: Dict[str, Any] = {
    "prev_hash": "genesis",
    "receipts": [],
    "max_receipts": 500,
}


def _lineage_path() -> str:
    primary = "/Volumes/NSExternal/ALEXANDRIA/validators/lineage.jsonl"
    fallback = os.path.expanduser("~/.axiolev/validators/lineage.jsonl")
    if os.path.isdir("/Volumes/NSExternal"):
        try:
            os.makedirs(os.path.dirname(primary), exist_ok=True)
            return primary
        except OSError:
            pass
    os.makedirs(os.path.dirname(fallback), exist_ok=True)
    return fallback


def emit_lineage_receipt(
    claim_id: str,
    domain: str,
    adapter: str,
    verdict: Verdict,
    confidence: float,
    checks: Dict[str, Any],
) -> tuple[str, str]:
    """Emit a Lineage Fabric receipt. Returns (receipt_id, lineage_hash)."""
    receipt_id = uuid.uuid4().hex
    payload: Dict[str, Any] = {
        "receipt_id": receipt_id,
        "prev_hash": _LINEAGE_STATE["prev_hash"],
        "claim_id": claim_id,
        "domain": domain,
        "adapter": adapter,
        "verdict": verdict,
        "confidence": confidence,
        "checks_summary": {k: str(v)[:80] for k, v in checks.items()},
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    lineage_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()
    payload["lineage_hash"] = lineage_hash

    _LINEAGE_STATE["prev_hash"] = lineage_hash
    buf: list = _LINEAGE_STATE["receipts"]
    buf.append(payload)
    if len(buf) > _LINEAGE_STATE["max_receipts"]:
        buf.pop(0)

    try:
        with open(_lineage_path(), "a") as fh:
            fh.write(json.dumps(payload) + "\n")
    except OSError:
        pass  # best-effort; receipt is in-memory ring regardless

    return receipt_id, lineage_hash


def cap_confidence(value: float) -> float:
    """Enforce I3 admin ceiling of 0.95."""
    return min(max(value, 0.0), I3_ADMIN_CAP)


def make_claim_id(claim: Dict[str, Any]) -> str:
    """Stable 16-char hex claim identifier derived from canonical JSON."""
    payload = json.dumps(claim, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]
