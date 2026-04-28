"""Gate P4 — NCOM dashboard acceptance tests.

REQUIRE:
  All 8 panels return valid dicts with panel key
  /ncom/healthz returns ok=True
  /ncom/panels lists all 8 panel IDs
  Each panel handler callable without error (empty ledger)
  Ledger health panel reports chain_valid for all tables
  Panel structure: each has 'ts' key
  FastAPI app imports without error
"""
from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from services.coherence_kernel.dashboard.panels import PANEL_HANDLERS
from services.coherence_kernel.dashboard.server import app

client = TestClient(app)

EXPECTED_PANELS = {
    "branch_registry", "decoherence_status", "readiness_score", "imo_queue",
    "interference_results", "ledger_health", "black_knight_status", "receipt_stream",
}


# ── panel handler unit tests ──────────────────────────────────────────────────

def test_exactly_8_panels_defined():
    assert set(PANEL_HANDLERS.keys()) == EXPECTED_PANELS


@pytest.mark.parametrize("panel_id", sorted(EXPECTED_PANELS))
def test_panel_handler_returns_dict(panel_id):
    handler = PANEL_HANDLERS[panel_id]
    result = handler()
    assert isinstance(result, dict)
    assert result.get("panel") == panel_id
    assert "ts" in result


def test_ledger_health_all_chains_valid():
    result = PANEL_HANDLERS["ledger_health"]()
    assert result["all_chains_valid"] is True
    for tbl, info in result["tables"].items():
        assert info["chain_valid"] is True, f"chain invalid for table {tbl}"


def test_imo_queue_structure():
    result = PANEL_HANDLERS["imo_queue"]()
    assert "pending_count" in result
    assert "pending_ids" in result
    assert "recent_decisions" in result


def test_readiness_score_handles_empty():
    result = PANEL_HANDLERS["readiness_score"]()
    assert "latest" in result


def test_receipt_stream_structure():
    result = PANEL_HANDLERS["receipt_stream"]()
    assert "receipts" in result
    assert isinstance(result["receipts"], list)


# ── HTTP endpoint tests ───────────────────────────────────────────────────────

def test_healthz():
    resp = client.get("/ncom/healthz")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_list_panels_endpoint():
    resp = client.get("/ncom/panels")
    assert resp.status_code == 200
    data = resp.json()
    assert set(data["panels"]) == EXPECTED_PANELS


@pytest.mark.parametrize("panel_id", sorted(EXPECTED_PANELS))
def test_panel_endpoint_200(panel_id):
    resp = client.get(f"/ncom/panels/{panel_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("panel") == panel_id


def test_panel_endpoint_404_unknown():
    resp = client.get("/ncom/panels/not_a_real_panel")
    assert resp.status_code == 404


def test_spa_root_returns_html():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
