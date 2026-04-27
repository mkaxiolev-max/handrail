"""PAP receipts — chained sha256 lineage, Alexandria-mirrored."""
import json
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
try:
    from ulid import ULID
    def _gen_id():
        return str(ULID())
except ImportError:
    import secrets
    def _gen_id():
        # Fallback: 26-char base32 random; not strict ULID but unique
        return secrets.token_hex(13).upper()

from .models import PAPReceipt, PAPDecision

RECEIPT_ROOT = Path(os.environ.get("PAP_RECEIPT_ROOT", ".run/pap/receipts"))


def _receipt_dir(now: datetime) -> Path:
    return RECEIPT_ROOT / f"{now.year:04d}" / f"{now.month:02d}" / f"{now.day:02d}"


def _last_receipt_hash() -> str:
    """Find most recent receipt's hash for chaining; '' if none."""
    if not RECEIPT_ROOT.exists():
        return ""
    candidates = sorted(RECEIPT_ROOT.rglob("*.json"))
    if not candidates:
        return ""
    latest = candidates[-1]
    try:
        return json.loads(latest.read_text()).get("hash", "")
    except Exception:
        return ""


def write_pap_receipt(
    resource_id: str,
    decision: PAPDecision,
    pap_score: float,
    aletheion_receipt_refs: Optional[List[str]] = None,
    handrail_receipt_ref: Optional[str] = None,
    qec_syndromes_fired: Optional[List[str]] = None,
    reasons: Optional[List[str]] = None,
) -> PAPReceipt:
    now = datetime.now(timezone.utc)
    rid = _gen_id()
    prev_hash = _last_receipt_hash()
    payload = {
        "receipt_type": "pap",
        "receipt_id": rid,
        "timestamp": now.isoformat(),
        "resource_id": resource_id,
        "decision": decision,
        "pap_score": pap_score,
        "aletheion_receipt_refs": aletheion_receipt_refs or [],
        "handrail_receipt_ref": handrail_receipt_ref,
        "qec_syndromes_fired": qec_syndromes_fired or [],
        "reasons": reasons or [],
        "prev_hash": prev_hash,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    h = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    payload["hash"] = h
    payload.pop("prev_hash")  # prev_hash is folded into the hash but not surfaced

    target_dir = _receipt_dir(now)
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / f"{rid}.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True)
    )

    return PAPReceipt(**payload)


def read_pap_receipt(receipt_id: str) -> Optional[PAPReceipt]:
    if not RECEIPT_ROOT.exists():
        return None
    for p in RECEIPT_ROOT.rglob(f"{receipt_id}.json"):
        return PAPReceipt(**json.loads(p.read_text()))
    return None
