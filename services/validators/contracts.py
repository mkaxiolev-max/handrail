"""Validator adapter contracts — AXIOLEV Holdings LLC © 2026.

Ontology: lineage via Lineage Fabric; storage via Alexandrian Archive.
I3 constraint: admin ceiling 95.0 — no adapter may return confidence > I3_ADMIN_CAP.
"""
from __future__ import annotations
import hashlib, json, os, time, uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Literal, Protocol

Verdict = Literal["PASS", "FAIL", "UNCERTAIN", "UNSUPPORTED"]

I3_ADMIN_CAP: float = 0.95  # I3 external admin ceiling — hard limit across all adapters


@dataclass
class ValidationResult:
    claim_id: str
    domain: str
    adapter: str
    verdict: Verdict
    confidence: float       # 0.0–I3_ADMIN_CAP; cap enforced by cap_confidence()
    rationale: str
    checks: Dict[str, Any]
    receipt_id: str
    lineage_hash: str
    ts: float = field(default_factory=time.time)

    def to_json(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"))


class ValidatorAdapter(Protocol):
    domain: str

    def validate(self, claim: str, context: Dict[str, Any]) -> ValidationResult: ...


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
    return min(value, I3_ADMIN_CAP)
