"""Deterministic JSON canonicalization + merkle root for PAP H/A/T linkage."""
import hashlib
import json
from typing import Any, Dict


def canonical_json(obj: Any) -> bytes:
    """Sorted keys, no whitespace, UTF-8. Determinism is mandatory."""
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, default=_json_default,
    ).encode("utf-8")


def _json_default(o):
    # datetimes -> iso8601; Pydantic models -> .dict() if available
    if hasattr(o, "isoformat"):
        return o.isoformat()
    if hasattr(o, "dict"):
        return o.dict()
    if hasattr(o, "model_dump"):
        return o.model_dump()
    raise TypeError(f"Cannot canonicalize {type(o)}")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def layer_hash(layer_obj: Any) -> str:
    if hasattr(layer_obj, "dict"):
        layer_obj = layer_obj.dict()
    elif hasattr(layer_obj, "model_dump"):
        layer_obj = layer_obj.model_dump()
    return sha256_hex(canonical_json(layer_obj))


def compute_merkle_root(H: Any, A: Any, T: Any) -> str:
    h = layer_hash(H)
    a = layer_hash(A)
    t = layer_hash(T)
    return sha256_hex((h + a + t).encode("utf-8"))


def verify_merkle_root(resource: Dict[str, Any]) -> bool:
    expected = compute_merkle_root(resource["H"], resource["A"], resource["T"])
    return expected == resource.get("merkle_root")
