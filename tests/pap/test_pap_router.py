from fastapi.testclient import TestClient


def _app():
    from fastapi import FastAPI
    from services.pap.router import pap_router
    app = FastAPI()
    app.include_router(pap_router)
    return app


def test_pap_healthz_returns_200():
    c = TestClient(_app())
    r = c.get("/pap/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["service"] == "pap"
    assert body["version"] == "1.0"


def _resource_json(r):
    if hasattr(r, "model_dump"):
        return r.model_dump(mode="json")
    import json
    from datetime import datetime
    def _default(o):
        if isinstance(o, datetime): return o.isoformat()
        raise TypeError(type(o))
    return json.loads(json.dumps(r.dict(), default=_default))


def test_pap_validate_clean_resource(clean_resource):
    c = TestClient(_app())
    r = c.post("/pap/validate", json=_resource_json(clean_resource))
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_pap_score_clean_resource(clean_resource):
    c = TestClient(_app())
    r = c.post("/pap/score", json=_resource_json(clean_resource))
    assert r.status_code == 200
    assert r.json()["score_total"] >= 90


def test_pap_canon_check_blocks_below_95():
    c = TestClient(_app())
    r = c.post("/pap/canon/check", json={
        "ldr_score": 100, "omega_gnoseo_score": 100, "pap_score": 92,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["canon_eligible"] is False
    assert body["blocking_track"] == "PAP"
