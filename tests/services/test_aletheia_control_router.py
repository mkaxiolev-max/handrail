import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from services.aletheia_control.router import router

@pytest.fixture
def client():
    app = FastAPI(); app.include_router(router); return TestClient(app)

def _inp():
    return {"input_id":"inp_aaaaaa","text":"I will commit the spec","source":"t",
            "urgency":0.5,"reversibility":0.5,"actor":"self"}

def test_classify(client):
    r = client.post("/aletheia-control/classify", json=_inp())
    assert r.status_code == 200; assert r.json()["circle"] in {"CONTROL","INFLUENCE","CONCERN","MIXED"}

def test_route(client):
    r = client.post("/aletheia-control/route", json=_inp()); assert r.status_code == 200

def test_dashboard(client):
    client.post("/aletheia-control/route", json=_inp())
    r = client.get("/aletheia-control/dashboard"); assert r.status_code == 200
    assert "control_ratio" in r.json()

def test_score(client):
    r = client.get("/aletheia-control/score"); assert r.status_code == 200
    assert "omega" in r.json()

def test_weekly_audit(client):
    r = client.post("/aletheia-control/weekly-audit"); assert r.status_code == 200
    assert "passed" in r.json()

def test_execute_control(client):
    atom = {"atom_id":"atm_abc123","input_id":"inp_aaaaaa","actor":"self",
            "verb":"commit","target":"spec","constraints":{},"expected_receipt":"receipt://x"}
    r = client.post("/aletheia-control/execute-control", json=atom); assert r.status_code == 200

def test_register_influence(client):
    chain = {"chain_id":"chn_abc123","input_id":"inp_aaaaaa","target_agent":"alex",
             "influence_action":"persuade","expected_conversion":0.7,
             "conversion_deadline":"2026-12-31T00:00:00+00:00"}
    r = client.post("/aletheia-control/register-influence", json=chain); assert r.status_code == 200

def test_delete_concern(client):
    rt = {"waste_id":"wst_abc123","input_id":"inp_aaaaaa","reason":"uncontrollable",
          "reingestion_cooldown_until":"2026-12-31T00:00:00+00:00","archived_to":"alexandria/waste"}
    r = client.post("/aletheia-control/delete-concern", json=rt); assert r.status_code == 200
