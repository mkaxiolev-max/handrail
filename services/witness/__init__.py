"""Witness cosigning service -- Rekor v2-pattern triad. AXIOLEV Holdings LLC (c) 2026."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Optional
import hashlib, hmac, json

@dataclass(frozen=True)
class STH:
    tree_size: int
    root_hash: str
    timestamp: int
    prev_root_hash: Optional[str] = None
    def canonical(self) -> bytes:
        return json.dumps(asdict(self), sort_keys=True, separators=(",",":")).encode()

@dataclass(frozen=True)
class Cosignature:
    witness_id: str
    sth_hash: str
    signature: str

@dataclass(frozen=True)
class CosignedSTH:
    sth: STH
    cosignatures: List[Cosignature]
    quorum: int
    def valid(self) -> bool:
        return len([c for c in self.cosignatures if c.signature]) >= self.quorum

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sth_hash(sth: STH) -> str:
    return sha256_hex(sth.canonical())

_KEYS = {
    "witness_alpha": b"axiolev-witness-alpha-key-2026",
    "witness_beta":  b"axiolev-witness-beta-key-2026",
    "witness_gamma": b"axiolev-witness-gamma-key-2026",
}

def cosign(sth: STH, witness_id: str) -> Cosignature:
    if witness_id not in _KEYS:
        raise ValueError(f"unknown witness {witness_id}")
    h = sth_hash(sth)
    sig = hmac.new(_KEYS[witness_id], h.encode(), hashlib.sha256).hexdigest()
    return Cosignature(witness_id=witness_id, sth_hash=h, signature=sig)

def verify(cs: Cosignature, sth: STH) -> bool:
    expected = sth_hash(sth)
    if cs.sth_hash != expected:
        return False
    key = _KEYS.get(cs.witness_id)
    if not key:
        return False
    want = hmac.new(key, expected.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(want, cs.signature)

def cosign_triad(sth: STH, quorum: int = 2) -> CosignedSTH:
    sigs: List[Cosignature] = []
    for wid in _KEYS.keys():
        try:
            sigs.append(cosign(sth, wid))
        except Exception:
            continue
    return CosignedSTH(sth=sth, cosignatures=sigs, quorum=quorum)

def verify_cosigned(cs: CosignedSTH) -> bool:
    valid = [c for c in cs.cosignatures if verify(c, cs.sth)]
    return len(valid) >= cs.quorum

def consistency_ok(prev: STH, curr: STH) -> bool:
    if curr.tree_size < prev.tree_size:
        return False
    if curr.prev_root_hash is not None and curr.prev_root_hash != prev.root_hash:
        return False
    return True
