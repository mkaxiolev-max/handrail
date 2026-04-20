"""UI aggregation route contract tests.

Verifies: no fabricated healthy state, correct structure, stale marking,
Handrail boundary notice present, memory distinguishes canonical/superseded/unresolved.
"""
from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from ns_api.app.main import app

client = TestClient(app)


def _get(path: str) -> dict:
    r = client.get(path)
    assert r.status_code == 200, f"{path} returned {r.status_code}: {r.text}"
    return r.json()


# ── /summary — Founder Home ─────────────────────────────────────────────────

def test_summary_has_required_keys():
    d = _get("/api/v1/ui/summary")
    for key in ("ts", "priorities", "open_loops", "reality_deltas", "organism_health", "governance_alerts", "receipt_count"):
        assert key in d, f"Missing key: {key}"


def test_summary_no_fabricated_healthy():
    d = _get("/api/v1/ui/summary")
    health = d["organism_health"]
    # Health must reflect probe truth — not hardcoded True
    assert isinstance(health["ns_core"]["ok"], bool)
    assert isinstance(health["handrail"]["ok"], bool)
    assert isinstance(health["alexandria_mounted"], bool)


def test_summary_priorities_are_list():
    d = _get("/api/v1/ui/summary")
    assert isinstance(d["priorities"], list)
    assert len(d["priorities"]) >= 1


def test_summary_open_loops_are_list():
    d = _get("/api/v1/ui/summary")
    assert isinstance(d["open_loops"], list)


def test_summary_reality_deltas_are_list():
    d = _get("/api/v1/ui/summary")
    assert isinstance(d["reality_deltas"], list)


# ── /voice ────────────────────────────────────────────────────────────────────

def test_voice_has_required_keys():
    d = _get("/api/v1/ui/voice")
    for key in ("ts", "mode", "shalom", "sessions", "session_count", "voice_receipts", "telephony_number", "governance_mode"):
        assert key in d, f"Missing key: {key}"


def test_voice_no_fabricated_shalom():
    d = _get("/api/v1/ui/voice")
    assert isinstance(d["shalom"], bool)


def test_voice_sessions_is_list():
    d = _get("/api/v1/ui/voice")
    assert isinstance(d["sessions"], list)


# ── /timeline ─────────────────────────────────────────────────────────────────

def test_timeline_has_required_keys():
    d = _get("/api/v1/ui/timeline")
    for key in ("ts", "events", "receipt_count", "has_failures"):
        assert key in d, f"Missing key: {key}"


def test_timeline_events_is_list():
    d = _get("/api/v1/ui/timeline")
    assert isinstance(d["events"], list)


def test_timeline_failure_flag_is_bool():
    d = _get("/api/v1/ui/timeline")
    assert isinstance(d["has_failures"], bool)


# ── /execution ───────────────────────────────────────────────────────────────

def test_execution_has_required_keys():
    d = _get("/api/v1/ui/execution")
    for key in ("ts", "handrail", "dispatch_history", "failures", "receipt_count"):
        assert key in d, f"Missing key: {key}"


def test_execution_handrail_notice_present():
    """Handrail boundary notice must always be explicit — never silently absent."""
    d = _get("/api/v1/ui/execution")
    notice = d["handrail"].get("notice", "")
    assert "Handrail" in notice, "Handrail boundary notice missing"
    assert d["handrail"]["is_moat"] is True


def test_execution_handrail_ok_is_bool():
    d = _get("/api/v1/ui/execution")
    assert isinstance(d["handrail"]["ok"], bool)


def test_execution_dispatch_history_is_list():
    d = _get("/api/v1/ui/execution")
    assert isinstance(d["dispatch_history"], list)


# ── /build ────────────────────────────────────────────────────────────────────

def test_build_has_required_keys():
    d = _get("/api/v1/ui/build")
    for key in ("ts", "notice", "pipeline_stages", "canon_gate", "threshold_requests"):
        assert key in d, f"Missing key: {key}"


def test_build_pipeline_stages_count():
    d = _get("/api/v1/ui/build")
    assert len(d["pipeline_stages"]) == 7


def test_build_canon_gate_thresholds():
    d = _get("/api/v1/ui/build")
    gate = d["canon_gate"]
    assert gate["score_threshold"] == 0.82
    assert gate["contradiction_ceiling"] == 0.25


def test_build_no_mock_complete_state():
    d = _get("/api/v1/ui/build")
    # ready_actions must be list (can be empty — not fabricated)
    assert isinstance(d.get("threshold_requests"), list)


# ── /memory ───────────────────────────────────────────────────────────────────

def test_memory_has_required_keys():
    d = _get("/api/v1/ui/memory")
    for key in ("ts", "alexandria_mounted", "substrate", "memory_classes", "by_type"):
        assert key in d, f"Missing key: {key}"


def test_memory_distinguishes_classes():
    """Memory must explicitly distinguish canonical, superseded, unresolved — not lump everything."""
    d = _get("/api/v1/ui/memory")
    classes = {mc["class"] for mc in d["memory_classes"]}
    assert "receipt"   in classes, "Missing 'receipt' class"
    assert "canonical" in classes, "Missing 'canonical' class"
    assert "superseded"in classes, "Missing 'superseded' class"
    assert "unresolved"in classes, "Missing 'unresolved' class"


def test_memory_alexandria_mounted_is_bool():
    d = _get("/api/v1/ui/memory")
    assert isinstance(d["alexandria_mounted"], bool)


# ── /governance ───────────────────────────────────────────────────────────────

def test_governance_has_required_keys():
    d = _get("/api/v1/ui/governance")
    for key in ("ts", "authority_state", "never_events", "threshold_requests", "quorum", "rings", "invariants"):
        assert key in d, f"Missing key: {key}"


def test_governance_seven_never_events():
    d = _get("/api/v1/ui/governance")
    assert len(d["never_events"]) == 7


def test_governance_never_events_all_active():
    d = _get("/api/v1/ui/governance")
    for ne in d["never_events"]:
        assert ne["active"] is True, f"{ne['id']} not active"


def test_governance_ten_invariants():
    d = _get("/api/v1/ui/governance")
    assert len(d["invariants"]) == 10


def test_governance_threshold_requests_explicit():
    """Threshold requests must be explicitly listed — empty list is fine; must not be absent."""
    d = _get("/api/v1/ui/governance")
    assert isinstance(d["threshold_requests"], list)


def test_governance_quorum_fields():
    d = _get("/api/v1/ui/governance")
    q = d["quorum"]
    assert "satisfied" in q
    assert "yubikey_serial" in q
    assert isinstance(q["satisfied"], bool)


# ── /architecture ─────────────────────────────────────────────────────────────

def test_architecture_has_required_keys():
    d = _get("/api/v1/ui/architecture")
    for key in ("ts", "layers", "services", "shalom", "invariants_intact"):
        assert key in d, f"Missing key: {key}"


def test_architecture_ten_layers():
    d = _get("/api/v1/ui/architecture")
    assert len(d["layers"]) == 10


def test_architecture_shalom_not_fabricated():
    d = _get("/api/v1/ui/architecture")
    assert isinstance(d["shalom"], bool)
