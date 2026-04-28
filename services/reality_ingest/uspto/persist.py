from __future__ import annotations
import hashlib, os
from datetime import datetime, timezone
from pathlib import Path
import orjson
from services.reality_ingest.schema import RealityObject, IngestionReceipt


def persist(obj: RealityObject, raw_root: Path, internal_root: Path,
            receipts_root: Path, stage_receipts: dict) -> IngestionReceipt:
    d = (obj.grant_date or datetime.now(timezone.utc)).strftime("%Y/%m/%d")
    canonical_path = raw_root / d / f"{obj.id}.json"
    internal_path  = internal_root / d / f"{obj.id}.json"
    receipt_path   = receipts_root / d / f"{obj.id}.receipt.json"
    body = obj.canonical_bytes()
    sha  = hashlib.sha256(body).hexdigest()
    _atomic_write(canonical_path, body)
    _atomic_write(internal_path, body)
    receipt = IngestionReceipt(
        receipt_id=f"RCT-{obj.id}-{int(datetime.now(timezone.utc).timestamp())}",
        object_id=obj.id, source="USPTO",
        epistemic_class=obj.epistemic_class,
        raw_sha256=sha, normalized_sha256=sha,
        fetch_receipt_id=stage_receipts.get("fetch", "?"),
        parse_receipt_id=stage_receipts.get("parse", "?"),
        normalize_receipt_id=stage_receipts.get("normalize", "?"),
        score_receipt_id=stage_receipts.get("score", "?"),
        persist_receipt_id=stage_receipts.get("persist", "?"),
        timestamp=datetime.now(timezone.utc),
    )
    _atomic_write(receipt_path,
                  orjson.dumps(receipt.model_dump(mode="json"),
                               option=orjson.OPT_SORT_KEYS | orjson.OPT_INDENT_2))
    return receipt


def _atomic_write(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("wb") as f:
        f.write(data); f.flush(); os.fsync(f.fileno())
    tmp.rename(path)
