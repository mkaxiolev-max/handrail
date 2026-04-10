from fastapi.testclient import TestClient

from app.main import app
from app.policy import guards as policy_guards
from app.routes import simulate as simulate_route


client = TestClient(app)


class FakeRepository:
    def __init__(self):
        self.created_run = None
        self.created_branches = None

    def create_run(self, run_record, *, input_payload, summary_payload, canon_version):
        self.created_run = {
            "run_record": run_record,
            "input_payload": input_payload,
            "summary_payload": summary_payload,
            "canon_version": canon_version,
        }

    def create_branches(self, run_id, branches):
        self.created_branches = {"run_id": run_id, "branches": branches}

    def write_summary_atom(self, run_record, summary_payload):
        return ["atom-omega-1"]

    def compare_run_to_observed(self, run_id, payload):
        return None


class FakeReceiptBridge:
    def issue_run_receipt(self, *, run_id, actor, input_payload, result_payload):
        return {
            "receipt_id": "rcpt_omega_1",
            "receipt_hash": "sha256:omega-test",
            "chain_verified": True,
        }


def test_simulate_route_returns_provisional_simulation(monkeypatch):
    fake_repo = FakeRepository()
    monkeypatch.setattr(simulate_route, "get_repository", lambda: fake_repo)
    monkeypatch.setattr(simulate_route, "get_receipt_bridge", lambda: FakeReceiptBridge())
    monkeypatch.setattr(policy_guards, "_hic_evaluate", lambda _: "R0")
    monkeypatch.setattr(simulate_route, "omega_hic_guard", policy_guards.omega_hic_guard)

    response = client.post(
        "/omega/simulate",
        json={
            "state_id": "state-demo-1",
            "domain_type": "commercial",
            "bounded_context": {"boundary": "pipeline"},
            "variables": {"demand": 10, "capacity": 8, "burn": 3},
            "constraints": {
                "demand": {"min": 5, "max": 16},
                "capacity": {"min": 6, "max": 14},
                "burn": {"min": 1, "max": 5},
            },
            "observables": {"demand": 10, "capacity": 8},
            "simulation_horizon": 4,
            "branch_count": 3,
            "metadata": {"seed": 7},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "simulated"
    assert body["provisional"] is True
    assert body["result_kind"] == "simulation"
    assert len(body["branches"]) == 3
    assert body["receipt_hash"] == "sha256:omega-test"
    assert body["chain_verified"] is True
    assert body["memory_atoms_written"] == 1
    assert body["summary"]["epistemic_boundary"]
    assert fake_repo.created_run is not None
    assert fake_repo.created_branches is not None


def test_simulate_accepts_founder_payload_shape(monkeypatch):
    fake_repo = FakeRepository()
    monkeypatch.setattr(simulate_route, "get_repository", lambda: fake_repo)
    monkeypatch.setattr(simulate_route, "get_receipt_bridge", lambda: FakeReceiptBridge())
    monkeypatch.setattr(policy_guards, "_hic_evaluate", lambda _: "R0")
    monkeypatch.setattr(simulate_route, "omega_hic_guard", policy_guards.omega_hic_guard)

    response = client.post(
        "/omega/simulate",
        json={
            "domain_type": "process",
            "bounded_context": "fundraising_pipeline",
            "variables": {"stage": "intro", "lead_quality": 0.7},
            "constraints": {"time_horizon": 3},
            "observables": ["response_rate"],
            "simulation_horizon": 3,
            "branch_count": 3,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["provisional"] is True
    assert body["result_kind"] == "simulation"
    assert body["summary"]["divergence_score"] >= 0
    assert "epistemic_boundary" in body["summary"]
    assert body["run_id"].startswith("omega_")


def test_simulate_blocks_execution_flags(monkeypatch):
    monkeypatch.setattr(policy_guards, "_hic_evaluate", lambda _: "R0")
    monkeypatch.setattr(simulate_route, "omega_hic_guard", policy_guards.omega_hic_guard)
    response = client.post(
        "/omega/simulate",
        json={
            "state_id": "omega-policy-veto",
            "domain_type": "commercial",
            "bounded_context": {"description": "attempt execute"},
            "variables": {"demand": 10},
            "constraints": {"allow_execution": True},
            "observables": {"demand": 10},
            "simulation_horizon": 2,
            "branch_count": 1,
            "metadata": {"actor": "founder:smoke"},
        },
    )
    assert response.status_code == 403
    assert response.json()["detail"]["policy_state"] == "vetoed"


def test_simulate_blocks_metadata_execute_and_promotion(monkeypatch):
    monkeypatch.setattr(policy_guards, "_hic_evaluate", lambda _: "R0")
    monkeypatch.setattr(simulate_route, "omega_hic_guard", policy_guards.omega_hic_guard)

    execution_response = client.post(
        "/omega/simulate",
        json={
            "domain_type": "process",
            "bounded_context": "fundraising_pipeline",
            "variables": {"stage": "intro"},
            "constraints": {},
            "observables": [],
            "simulation_horizon": 2,
            "branch_count": 2,
            "metadata": {"action": "send_email", "execute": True},
        },
    )
    assert execution_response.status_code == 403
    assert execution_response.json()["detail"]["policy_state"] == "vetoed"

    promotion_response = client.post(
        "/omega/simulate",
        json={
            "domain_type": "policy",
            "bounded_context": "governance",
            "variables": {"proposal": "promote_to_canon"},
            "constraints": {},
            "observables": [],
            "simulation_horizon": 1,
            "branch_count": 1,
            "metadata": {"canon_promote": True},
        },
    )
    assert promotion_response.status_code == 403
    assert promotion_response.json()["detail"]["policy_state"] == "vetoed"
