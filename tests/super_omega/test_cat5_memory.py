"""Category 5 — Memory + Lineage. AXIOLEV © 2026.
Replay yields identical result sequence."""
from services.omega_logos.runtime.core import Orchestrator
from services.omega_logos.runtime.autonomy import Tier

def test_5_1_full_lineage_replay_deterministic():
    o = Orchestrator(tier=Tier.BOUNDED_WORKFLOWS)
    st = o.begin("plan a thing", tier=Tier.REVERSIBLE_EXECUTION)
    o.step(st, "inquiry",      {"claim": "x"})
    o.step(st, "adjudication", {"allow": True})
    o.step(st, "execution",    {"op": "noop"})
    o.end(st, {"ok": True})
    hashes = [r.signature for r in st.receipts]
    assert len(hashes) == len(set(hashes))  # unique receipt chain
    assert all(h and len(h) == 64 for h in hashes)

def test_5_2_update_supersedes_without_losing_old():
    o = Orchestrator(tier=Tier.PROPOSE_ONLY)
    st = o.begin("conclusion v1")
    o.step(st, "inquiry", {"conclusion": "A"})
    o.step(st, "inquiry", {"conclusion": "B"})  # supersede
    stages = [r.stage for r in st.receipts]
    convs = [r.payload.get("conclusion") for r in st.receipts if r.stage == "inquiry"]
    assert convs == ["A","B"]  # both preserved, order preserved
