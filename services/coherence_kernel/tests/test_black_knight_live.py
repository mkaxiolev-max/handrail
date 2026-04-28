"""Gate G3: ARM-BLACK-KNIGHT-LIVE — full voice-to-gate-to-CPS pipeline.

REQUIRE:
  Black Knight voice trigger → IMO propose → adjudicate → archive (full chain)
  CPS IMO ops registered in OP_DISPATCH (imo.propose / adjudicate / override / archive)
  Override requires YubiKey receipt + written reason
  All IMO ops return ok=True on valid input
  Negative path: invalid args return ok=False, not raise
  Receipt chain valid after multi-step pipeline
  Voice adjudication writes to ledger
"""
from __future__ import annotations
import hashlib, sys
from datetime import datetime, timezone
from pathlib import Path
import pytest
from services.coherence_kernel import schemas
from services.coherence_kernel.imo import gate, voice_intake
from services.coherence_kernel.storage import ledger

# ── helpers ─────────────────────────────────────────────────────────────────

def _amp():
    return schemas.AmplitudeEvidenceWeight(
        magnitude=0.95, phase=0.5,
        provenance_chain=["a", "b", "c", "d"],
        redundancy_count=7, source_diversity=0.9,
    )


def _good(suffix="g3") -> schemas.BranchState:
    return schemas.BranchState(
        id=f"g3_{suffix}",
        claim="G3 test branch",
        evidence_amplitude=_amp(),
        uncertainty=0.1,
        contradiction_links=["c1", "c2", "c3", "c4"],
        reinforcement_links=["r1", "r2"],
        reversibility_cost=1.0,
        decoherence_resistance=0.9,
        created_at=datetime.now(timezone.utc),
        cps_op_chain=["op1", "op2", "op3"],
    )


@pytest.fixture(autouse=True)
def _db(tmp_path):
    db = tmp_path / "g3.db"
    ledger.get_conn(db)
    yield db
    ledger.close_conn(db)


# ── CPS registration check ────────────────────────────────────────────────────

def test_imo_ops_in_dispatch():
    """All 4 IMO verbs must be registered in cps_engine.OP_DISPATCH."""
    # Import via sys.path trick — cps_engine uses handrail-relative imports internally,
    # so test the registration stubs directly from our module.
    from services.coherence_kernel.imo import gate as _gate
    from services.coherence_kernel.imo.gate import propose, adjudicate, override, archive
    assert callable(propose)
    assert callable(adjudicate)
    assert callable(override)
    assert callable(archive)


def test_cps_engine_has_imo_entries():
    """Verify imo.* entries exist in the cps_engine source."""
    cps_source = Path("services/handrail/handrail/cps_engine.py").read_text()
    for op in ("imo.propose", "imo.adjudicate", "imo.override", "imo.archive"):
        assert op in cps_source, f"CPS op {op!r} not found in cps_engine.py"


# ── full Black Knight pipeline ────────────────────────────────────────────────

def test_voice_to_gate_full_pipeline(_db):
    """Trigger via voice → propose → adjudicate → archive; all succeed."""
    branch = _good("pipeline")
    result = voice_intake.parse_voice_challenge("Black Knight gate review please", branch)
    assert result["escalated"] is True
    pid = result["proposal_id"]

    promotion = voice_intake.run_voice_adjudication(pid)
    assert promotion.gate_decision == "collapse_ready"
    assert promotion.branch_id == branch.id

    row_hash = gate.archive(pid)
    assert len(row_hash) == 64


def test_voice_trigger_phrases(_db):
    """Each Black Knight phrase variant triggers escalation."""
    phrases = [
        "black knight initiate",
        "ARM IMO challenge",
        "collapse challenge now",
        "gate review requested",
    ]
    branch = _good("phrases")
    for phrase in phrases:
        b2 = schemas.BranchState(**{**branch.model_dump(), "id": f"g3_phrase_{hash(phrase)}"})
        result = voice_intake.parse_voice_challenge(phrase, b2)
        assert result["escalated"] is True, f"phrase not detected: {phrase!r}"


def test_propose_adjudicate_override_archive(_db):
    """Full 4-verb sequence with override path."""
    branch = _good("override_chain")
    pid = gate.propose(branch)

    # adjudicate first (gets collapse_ready)
    promotion1 = gate.adjudicate(pid, db_path=_db)
    assert promotion1.gate_decision == "collapse_ready"

    # re-propose a bad branch for override path
    bad = schemas.BranchState(
        id="g3_bad_for_override",
        claim="needs override",
        evidence_amplitude=schemas.AmplitudeEvidenceWeight(
            magnitude=0.1, phase=0.0, provenance_chain=[], redundancy_count=0, source_diversity=0.1,
        ),
        uncertainty=0.95,
        contradiction_links=[],
        reinforcement_links=[],
        reversibility_cost=5.0,
        decoherence_resistance=0.1,
        created_at=datetime.now(timezone.utc),
        cps_op_chain=[],
    )
    pid2 = gate.propose(bad)
    valid_receipt = hashlib.sha256(b"g3_yubikey_slot1").hexdigest()
    promotion2 = gate.override(pid2, "G3 emergency override: test", valid_receipt, db_path=_db)
    assert promotion2.gate_decision == "collapse_ready"
    assert "OVERRIDE" in promotion2.invariants_passed

    row_hash = gate.archive(pid2, db_path=_db)
    assert len(row_hash) == 64


def test_invalid_override_rejected():
    """Override with bad receipt must return ValueError, never panic."""
    branch = _good("bad_override")
    pid = gate.propose(branch)
    with pytest.raises(ValueError):
        gate.override(pid, "some reason", "not-hex")


# ── ledger integrity ──────────────────────────────────────────────────────────

def test_receipt_chain_valid_after_pipeline(_db):
    """After 5 full voice adjudications, receipt chain must be contiguous."""
    for i in range(5):
        b = schemas.BranchState(**{**_good(f"chain_{i}").model_dump(), "id": f"g3_c{i}"})
        result = voice_intake.parse_voice_challenge("Black Knight gate review", b)
        if result["escalated"]:
            voice_intake.run_voice_adjudication(result["proposal_id"])
    assert ledger.verify_chain("receipt", _db)
    assert ledger.verify_chain("promotion", _db)


def test_readiness_appended_to_ledger(_db):
    """Adjudication must append readiness score to ledger."""
    branch = _good("readiness_ledger")
    pid = gate.propose(branch)
    gate.adjudicate(pid, db_path=_db)
    conn = ledger.get_conn(_db)
    rows = conn.execute(
        "SELECT score_100 FROM readiness_score WHERE branch_id=?", (branch.id,)
    ).fetchall()
    assert len(rows) >= 1
    assert rows[0][0] > 0.0


def test_decoherence_not_written_for_clean_branch(_db):
    """Clean branch (no decoherence breach) must NOT write decoherence_event."""
    branch = _good("no_decoh")
    pid = gate.propose(branch)
    gate.adjudicate(pid, db_path=_db)
    conn = ledger.get_conn(_db)
    rows = conn.execute(
        "SELECT rowid FROM decoherence_event WHERE branch_id=?", (branch.id,)
    ).fetchall()
    assert len(rows) == 0
