from tools.ns_test_ontology.ontology import build_ontology, discover_pytest_tests


def test_external_verifiability_has_minimum_floor():
    ontology = build_ontology(discover_pytest_tests())
    assert ontology["instrument_totals"].get("I3", 0) >= 50


def test_validator_systems_are_i3_mapped():
    ontology = build_ontology(discover_pytest_tests())
    validator_tests = [
        obj for obj in ontology["objects"]
        if "tests/validators/" in obj["file_path"] or "test_validators.py" in obj["file_path"]
    ]
    assert validator_tests
    assert all(obj["instrument"] == "I3" for obj in validator_tests)


def test_external_gate_tests_are_i3_mapped():
    ontology = build_ontology(discover_pytest_tests())
    gate_tests = [obj for obj in ontology["objects"] if "test_ring5_external" in obj["file_path"]]
    assert gate_tests
    assert all(obj["instrument"] == "I3" for obj in gate_tests)


def test_brokerage_tests_are_i3_mapped():
    ontology = build_ontology(discover_pytest_tests())
    brokerage_tests = [obj for obj in ontology["objects"] if "tests/brokerage/" in obj["file_path"]]
    assert brokerage_tests
    assert all(obj["instrument"] == "I3" for obj in brokerage_tests)


def test_i3_not_below_certification_threshold():
    ontology = build_ontology(discover_pytest_tests())
    assert ontology["instrument_totals"].get("I3", 0) >= 50
