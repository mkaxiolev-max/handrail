"""Category 6 — Governance. AXIOLEV © 2026.
Canon bypass is denied. High-risk actions escalate."""
from services.omega_logos.layers.adjudication import adjudicate

def test_6_1_canon_bypass_denied():
    d = adjudicate({"subject":"anon","action":"canon.promote","resource":"canon"})
    assert d.allow is False and d.code == "CANON_PROMOTION_DENIED"

def test_6_2_live_key_in_args_triggers_dignity_violation():
    fake_key = "sk_" + "live_abc123"  # gitleaks:allow — intentional test fixture, not a real key
    d = adjudicate({"action":"ops.dispatch","args":f"token={fake_key}"})
    assert d.allow is False and d.code == "DIGNITY_KERNEL_VIOLATION"
