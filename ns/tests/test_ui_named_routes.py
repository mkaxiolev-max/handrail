"""axiolev-ui-routes-test-v2"""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ns.services.ui.router import ui_router


def _client():
    app = FastAPI()
    app.include_router(ui_router)
    return TestClient(app)


def test_ns_state_layers():
    c = _client()
    r = c.get("/ns/state")
    assert r.status_code == 200
    body = r.json()
    assert "layers" in body
    assert len(body["layers"]) == 10
    assert body["layers"]["L2"]["name"] == "Gradient Field"
    assert body["layers"]["L5"]["name"] == "Alexandrian Lexicon"
    assert body["layers"]["L7"]["name"] == "Alexandrian Archive"
    assert body["layers"]["L8"]["name"] == "Lineage Fabric"


def test_program_list_contains_core_four():
    c = _client()
    body = c.get("/program/list").json()
    ids = {p["id"] for p in body["programs"]}
    assert {"ns_core", "handrail", "continuum", "state_api"}.issubset(ids)


def test_program_detail_404_on_unknown():
    c = _client()
    r = c.get("/program/unknown_xyz")
    assert r.status_code == 404


def test_receipt_404_on_unknown():
    c = _client()
    r = c.get("/receipt/zzz_does_not_exist_zzz")
    assert r.status_code == 404


def test_canon_view_shape():
    c = _client()
    body = c.get("/canon").json()
    assert "rule_count" in body
    assert "warning" in body


def test_governance_state_invariants_ten():
    c = _client()
    body = c.get("/governance/state").json()
    assert len(body["invariants"]) == 10
    assert "I4" in body["invariants"]
    assert "26116460" in body["invariants"]["I4"]
    assert "Alexandrian Archive remembers" in body["doctrine"]


def test_projection_invariance_ns_state():
    c = _client()
    a = c.get("/ns/state").json()
    b = c.get("/ns/state").json()
    a.pop("ts", None); b.pop("ts", None)
    assert a == b


def test_projection_invariance_governance_state():
    c = _client()
    a = c.get("/governance/state").json()
    b = c.get("/governance/state").json()
    a.pop("ts", None); b.pop("ts", None)
    assert a == b
