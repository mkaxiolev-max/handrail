"""Governance layer — binds Ω-Logos to NS∞ canon/HIC/PDP.
AXIOLEV Holdings LLC © 2026. (Maps to I₆.C2 — canon_integrity_preservation.)"""
import urllib.request as R
import json, urllib.error

NS_CORE = "http://127.0.0.1:9000"

def _get(path: str, timeout: float = 3.0):
    try:
        with R.urlopen(NS_CORE + path, timeout=timeout) as r: return json.loads(r.read())
    except Exception: return None

def canon_enforced() -> dict:
    return _get("/canon/invariants") or {"invariants": [], "enforced_count": 0}

def hic_gates() -> dict:
    return _get("/hic/gates") or {}

def pdp_is_available() -> bool:
    return _get("/violet/status") is not None
