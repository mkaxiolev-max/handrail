from tools.ns_test_ontology.ontology import build_ontology, discover_pytest_tests, score_from_ontology


def test_all_pytest_tests_are_classified():
    ontology = build_ontology(discover_pytest_tests())
    assert ontology["unmapped"] == []


def test_every_test_maps_to_valid_instrument():
    ontology = build_ontology(discover_pytest_tests())
    valid = {"I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8"}
    bad = [obj for obj in ontology["objects"] if obj["instrument"] not in valid]
    assert bad == []


def test_i7_certification_power_is_test_backed():
    ontology = build_ontology(discover_pytest_tests())
    assert ontology["instrument_totals"].get("I7", 0) >= 20


def test_i3_external_verifiability_minimum_coverage():
    ontology = build_ontology(discover_pytest_tests())
    assert ontology["instrument_totals"].get("I3", 0) >= 50


def test_score_report_has_no_critical_traceability_gaps():
    ontology = build_ontology(discover_pytest_tests())
    score = score_from_ontology(ontology)
    critical = [g for g in score["gaps"] if g["severity"] == "CRITICAL"]
    assert critical == []
