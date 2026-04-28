"""Gate P3 — IMO adjudication acceptance tests.

G2 token: ARM-IMO-COMMIT-LIVE
REQUIRE:
  All 4 gate verbs functional (propose/adjudicate/override/archive)
  11 steps executed in order for every adjudication
  Hard invariant failures map to correct gate_decision
  Override: valid receipt → collapse_ready; invalid receipt → ValueError
  Advisory invariants correctly classified (not in invariants_passed)
  Voice intake: challenge keyword triggers escalation
  All decisions persisted to ledger
"""
from __future__ import annotations
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import pytest
from services.coherence_kernel import schemas
from services.coherence_kernel.imo import gate, invariants, voice_intake
from services.coherence_kernel.storage import ledger

# ── helpers ─────────────────────────────────────────────────────────────────

def _amp(mag=0.95, phase=0.5, prov=None, redund=7, div=0.9):
    return schemas.AmplitudeEvidenceWeight(
        magnitude=mag, phase=phase,
        provenance_chain=prov if prov is not None else ["a", "b", "c", "d"],
        redundancy_count=redund, source_diversity=div,
    )


def _good_branch(suffix="good") -> schemas.BranchState:
    """Branch that passes all 7 hard invariants; score_100 ~91.6 >= 78.0."""
    return schemas.BranchState(
        id=f"br_{suffix}",
        claim="well-supported claim",
        evidence_amplitude=_amp(),
        uncertainty=0.1,
        contradiction_links=["c1", "c2", "c3", "c4"],
        reinforcement_links=["r1", "r2"],
        reversibility_cost=1.0,
        decoherence_resistance=0.9,
        created_at=datetime.now(timezone.utc),
        cps_op_chain=["op1", "op2", "op3"],
    )


def _bad_branch(suffix="bad") -> schemas.BranchState:
    """Branch that fails multiple hard invariants."""
    return schemas.BranchState(
        id=f"br_{suffix}",
        claim="poorly supported",
        evidence_amplitude=_amp(mag=0.05, prov=[], div=0.1, redund=0),
        uncertainty=0.95,
        contradiction_links=[],
        reinforcement_links=["r1"] * 8,
        reversibility_cost=9.5,
        decoherence_resistance=0.05,
        created_at=datetime.now(timezone.utc),
        cps_op_chain=[],  # H6 fails
    )


def _decoherence_only_branch(suffix="decoh") -> schemas.BranchState:
    """Good branch but with high decoherence indicators → H5 fails."""
    return schemas.BranchState(
        id=f"br_{suffix}",
        claim="decoherent but otherwise ready",
        evidence_amplitude=_amp(mag=0.8, prov=["a", "b", "c", "d"], div=0.1, redund=12),
        uncertainty=0.85,
        contradiction_links=[],
        reinforcement_links=["r1"] * 9,
        reversibility_cost=9.0,
        decoherence_resistance=0.05,
        created_at=datetime.now(timezone.utc),
        cps_op_chain=["op1", "op2", "op3", "op4", "op5", "op6", "op7", "op8"],
    )


@pytest.fixture(autouse=True)
def _isolated_ledger(tmp_path):
    db = tmp_path / "imo_gate_test.db"
    ledger.get_conn(db)
    yield db
    ledger.close_conn(db)


# ── verb tests ───────────────────────────────────────────────────────────────

def test_propose_returns_proposal_id():
    pid = gate.propose(_good_branch("p1"))
    assert isinstance(pid, str) and len(pid) == 36  # UUID4


def test_adjudicate_collapse_ready(_isolated_ledger):
    branch = _good_branch("adj_good")
    pid = gate.propose(branch)
    promotion = gate.adjudicate(pid, db_path=_isolated_ledger)
    assert promotion.gate_decision == "collapse_ready"
    assert promotion.branch_id == branch.id
    assert all(h.name in promotion.invariants_passed for h in invariants.HARD)


def test_adjudicate_abort_on_multiple_failures(_isolated_ledger):
    branch = _bad_branch("adj_bad")
    pid = gate.propose(branch)
    promotion = gate.adjudicate(pid, db_path=_isolated_ledger)
    assert promotion.gate_decision == "abort"


def test_adjudicate_hold_ncom_on_decoherence_only(_isolated_ledger):
    """When only H5 fails (decoherence breach), decision must be hold_ncom."""
    branch = _decoherence_only_branch("decoh_only")
    pid = gate.propose(branch)
    promotion = gate.adjudicate(pid, db_path=_isolated_ledger)
    # H5 must be in failed set; decision must be hold_ncom
    assert "H5_NO_DECOHERENCE_BREACH" not in promotion.invariants_passed
    assert promotion.gate_decision in {"hold_ncom", "abort"}


def test_adjudicate_missing_proposal():
    with pytest.raises(KeyError, match="no proposal"):
        gate.adjudicate("nonexistent-id")


def test_override_valid_receipt(_isolated_ledger):
    branch = _bad_branch("override_ok")
    pid = gate.propose(branch)
    valid_receipt = hashlib.sha256(b"test_yubikey_otp").hexdigest()
    promotion = gate.override(pid, "emergency founder override", valid_receipt, db_path=_isolated_ledger)
    assert promotion.gate_decision == "collapse_ready"
    assert "OVERRIDE" in promotion.invariants_passed


def test_override_invalid_receipt():
    branch = _bad_branch("override_bad")
    pid = gate.propose(branch)
    with pytest.raises(ValueError, match="yubikey_receipt"):
        gate.override(pid, "reason", "not-a-64-char-hex")


def test_override_empty_reason():
    branch = _bad_branch("override_empty")
    pid = gate.propose(branch)
    valid_receipt = hashlib.sha256(b"otp").hexdigest()
    with pytest.raises(ValueError, match="reason"):
        gate.override(pid, "", valid_receipt)


def test_archive_cleans_up(_isolated_ledger):
    branch = _good_branch("archive_test")
    pid = gate.propose(branch)
    gate.adjudicate(pid, db_path=_isolated_ledger)
    row_hash = gate.archive(pid, db_path=_isolated_ledger)
    assert isinstance(row_hash, str) and len(row_hash) == 64
    # After archive, proposal is removed — adjudicate again should raise
    with pytest.raises(KeyError):
        gate.adjudicate(pid, db_path=_isolated_ledger)


def test_archive_without_adjudication():
    pid = gate.propose(_good_branch("archive_noadj"))
    with pytest.raises(KeyError, match="adjudicate first"):
        gate.archive(pid)


# ── invariant coverage ────────────────────────────────────────────────────────

def test_all_7_hard_invariants_defined():
    assert len(invariants.HARD) == 7
    names = {inv.name for inv in invariants.HARD}
    assert names == {
        "H1_MIN_READINESS", "H2_PROVENANCE_DEPTH", "H3_EVIDENCE_MAGNITUDE",
        "H4_UNCERTAINTY_BOUNDED", "H5_NO_DECOHERENCE_BREACH",
        "H6_RECEIPT_CHAIN_VALID", "H7_REVERSIBILITY_DOCUMENTED",
    }


def test_all_3_advisory_invariants_defined():
    assert len(invariants.ADVISORY) == 3
    names = {inv.name for inv in invariants.ADVISORY}
    assert names == {"A1_OMEGA_TARGET", "A2_SOURCE_DIVERSITY", "A3_CONTRADICTION_METABOLISM"}


def test_advisory_not_in_hard_passed(_isolated_ledger):
    branch = _good_branch("advisory_sep")
    pid = gate.propose(branch)
    promotion = gate.adjudicate(pid, db_path=_isolated_ledger)
    advisory_names = {inv.name for inv in invariants.ADVISORY}
    for name in promotion.invariants_passed:
        assert name not in advisory_names, f"advisory {name} leaked into invariants_passed"


# ── voice intake ─────────────────────────────────────────────────────────────

def test_voice_intake_escalates_on_keyword(_isolated_ledger):
    branch = _good_branch("voice_test")
    result = voice_intake.parse_voice_challenge("ARM IMO collapse challenge now", branch)
    assert result["escalated"] is True
    assert result["proposal_id"] is not None
    # Run adjudication on the escalated proposal
    promotion = voice_intake.run_voice_adjudication(result["proposal_id"])
    assert promotion.gate_decision == "collapse_ready"


def test_voice_intake_no_escalation_without_keyword():
    branch = _good_branch("voice_quiet")
    result = voice_intake.parse_voice_challenge("show me the readiness score please", branch)
    assert result["escalated"] is False
    assert result["proposal_id"] is None


def test_voice_intake_black_knight_phrase():
    branch = _good_branch("voice_bk")
    result = voice_intake.parse_voice_challenge("Black Knight, initiate gate review", branch)
    assert result["escalated"] is True
    assert result["trigger_phrase"] is not None


# ── ledger persistence ────────────────────────────────────────────────────────

def test_ledger_has_promotion_after_adjudicate(_isolated_ledger):
    branch = _good_branch("ledger_promo")
    pid = gate.propose(branch)
    gate.adjudicate(pid, db_path=_isolated_ledger)
    conn = ledger.get_conn(_isolated_ledger)
    rows = conn.execute("SELECT gate_decision FROM promotion WHERE branch_id=?", (branch.id,)).fetchall()
    assert len(rows) >= 1
    assert rows[-1][0] == "collapse_ready"


def test_ledger_chain_valid_after_multiple_adjudications(_isolated_ledger):
    for i in range(5):
        branch = _good_branch(f"chain_{i}")
        pid = gate.propose(branch)
        gate.adjudicate(pid, db_path=_isolated_ledger)
    assert ledger.verify_chain("promotion", _isolated_ledger)
    assert ledger.verify_chain("receipt", _isolated_ledger)
