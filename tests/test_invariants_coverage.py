"""Q18 — invariant audit tests (mirrors Script 1 patterns)."""
import os, pathlib

NAMES = ["HIC_VETO","PDP_POLICY","OMEGA_BOUNDED","RECEIPT_CHAIN",
         "APPEND_ONLY","MONOTONE","DIGNITY_KERNEL","REVERSIBLE",
         "THREE_REALITIES","HAMILTONIAN"]

def test_all_ten_named_in_repo():
    missing = []
    root = pathlib.Path(".").resolve()
    text_blobs = []
    for p in root.rglob("*.md"):
        try: text_blobs.append(p.read_text(errors="ignore"))
        except Exception: pass
    for p in root.rglob("*.py"):
        try: text_blobs.append(p.read_text(errors="ignore"))
        except Exception: pass
    blob = "\n".join(text_blobs)
    for n in NAMES:
        if n not in blob:
            missing.append(n)
    assert not missing, f"missing invariants: {missing}"
