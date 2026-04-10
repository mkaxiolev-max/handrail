from fastapi.testclient import TestClient

from app.main import app
from app.policy import guards as policy_guards
from app.routes import runs as runs_route


client = TestClient(app)


class FakeRunsRepository:
    def list_runs(self, limit=20):
        return [{"run_id": "omega_1", "status": "simulated", "provisional": True}]

    def get_run(self, run_id: str):
        if run_id != "omega_1":
            return None
        return {
            "run_id": run_id,
            "summary_payload": {"most_likely_branch": "omega_1_b0"},
            "status": "simulated",
        }

    def get_branches(self, run_id: str):
        if run_id != "omega_1":
            return []
        return [
            {
                "branch_id": "omega_1_b0",
                "branch_index": 0,
                "outputs": {"final_state": {"x": 1.0, "y": 2.0}},
                "likelihood": 0.6,
            },
            {
                "branch_id": "omega_1_b1",
                "branch_index": 1,
                "outputs": {"final_state": {"x": 4.0, "y": 5.0}},
                "likelihood": 0.4,
            },
        ]

    def compare_run_to_observed(self, run_id: str, payload: dict):
        if run_id != "omega_1":
            return None
        return {
            "run_id": run_id,
            "status": "compared",
            "result_kind": "simulation_comparison",
            "provisional": True,
            "best_match_branch": "omega_1_b0",
            "reality_gap": 0.1,
            "comparisons": [{"branch_id": "omega_1_b0", "total_delta": 0.1}],
            "warnings": [],
        }


def test_list_runs(monkeypatch):
    monkeypatch.setattr(runs_route, "get_repository", lambda: FakeRunsRepository())
    response = client.get("/omega/runs")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_compare_run(monkeypatch):
    monkeypatch.setattr(runs_route, "get_repository", lambda: FakeRunsRepository())
    monkeypatch.setattr(policy_guards, "_pdp_decide", lambda subject, action, resource: "ALLOW")
    monkeypatch.setattr(runs_route, "omega_pdp_guard", policy_guards.omega_pdp_guard)
    response = client.post(
        "/omega/runs/omega_1/compare",
        json={"observed_state": {"x": 1.0, "y": 2.1}},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["result_kind"] == "simulation_comparison"
    assert body["provisional"] is True
    assert body["best_match_branch"] == "omega_1_b0"


def test_compare_run_denies_guest(monkeypatch):
    monkeypatch.setattr(runs_route, "get_repository", lambda: FakeRunsRepository())
    monkeypatch.setattr(policy_guards, "_pdp_decide", lambda subject, action, resource: "DENY")
    monkeypatch.setattr(runs_route, "omega_pdp_guard", policy_guards.omega_pdp_guard)
    response = client.post(
        "/omega/runs/omega_1/compare",
        json={"observed_outcome": {"operator": "guest"}, "observed_state": {"x": 1.0}},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["policy_state"] == "denied"
