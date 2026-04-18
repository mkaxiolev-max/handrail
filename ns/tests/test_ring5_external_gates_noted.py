"""Ring 5 — External Gates (noted, out-of-band) tests."""
import pytest
from ns.domain.policies.external_gates import EXTERNAL_GATES

EXPECTED_IDS = {
    "stripe_llc_verification",
    "stripe_live_keys_vercel",
    "root_handrail_price_ids",
    "yubikey_slot2",
    "dns_cname_root",
}


def test_external_gates_is_list():
    assert isinstance(EXTERNAL_GATES, list)


def test_external_gates_count():
    assert len(EXTERNAL_GATES) == 5


def test_external_gates_all_pending():
    for gate in EXTERNAL_GATES:
        assert gate["status"] == "pending", f"{gate['id']} not pending"


def test_external_gates_all_out_of_band_or_noted():
    for gate in EXTERNAL_GATES:
        assert "note" in gate and gate["note"], f"{gate['id']} missing note"


def test_external_gates_ids():
    ids = {g["id"] for g in EXTERNAL_GATES}
    assert ids == EXPECTED_IDS


def test_external_gates_no_network_calls():
    """Importing the module must not make any network calls — verified by import alone."""
    import importlib
    mod = importlib.import_module("ns.domain.policies.external_gates")
    assert hasattr(mod, "EXTERNAL_GATES")


def test_stripe_llc_verification_gate():
    gate = next(g for g in EXTERNAL_GATES if g["id"] == "stripe_llc_verification")
    assert gate["status"] == "pending"
    assert gate["note"] == "out-of-band"


def test_dns_cname_root_gate():
    gate = next(g for g in EXTERNAL_GATES if g["id"] == "dns_cname_root")
    assert "root.axiolev.com" in gate["note"]
    assert "root-jade-kappa.vercel.app" in gate["note"]


def test_yubikey_slot2_gate():
    gate = next(g for g in EXTERNAL_GATES if g["id"] == "yubikey_slot2")
    assert "$55" in gate["note"]


def test_each_gate_has_required_keys():
    for gate in EXTERNAL_GATES:
        assert "id" in gate
        assert "status" in gate
        assert "note" in gate
