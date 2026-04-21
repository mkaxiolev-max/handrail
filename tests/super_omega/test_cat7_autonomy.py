"""Category 7 — Autonomy. AXIOLEV © 2026.
Tier request is clamped to ceiling. No drift in 24h-stub workflow."""
from services.omega_logos.runtime.autonomy import Tier, gate, DEFAULT_CEILING
from services.omega_logos.runtime.core import Orchestrator

def test_7_1_tier_clamped_to_ceiling():
    assert gate(Tier.STRATEGIC) == DEFAULT_CEILING

def test_7_2_stub_long_horizon_no_drift():
    o = Orchestrator(tier=Tier.BOUNDED_WORKFLOWS)
    st = o.begin("24h workflow stub")
    for i in range(50):
        o.step(st, "execution", {"i": i, "op": "noop"})
    o.end(st, {"ok": True})
    # Signatures must remain unique and well-formed
    sigs = [r.signature for r in st.receipts]
    assert len(sigs) == len(set(sigs)) and all(len(s) == 64 for s in sigs)
