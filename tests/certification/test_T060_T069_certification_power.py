from tools.ns_test_ontology.ontology import INSTRUMENTS, RULES, build_ontology, discover_pytest_tests, score_from_ontology


def test_T060_governance_category_exists():
    assert "I7" in INSTRUMENTS
    assert "Certification" in INSTRUMENTS["I7"]["name"]


def test_T061_i7_has_rule_coverage():
    assert any(rule[0] == "I7" for rule in RULES)


def test_T062_claim_to_test_traceability_exists():
    ontology = build_ontology(discover_pytest_tests())
    assert ontology["instrument_totals"].get("I7", 0) > 0


def test_T063_no_unmapped_tests_for_certification():
    ontology = build_ontology(discover_pytest_tests())
    assert len(ontology["unmapped"]) == 0


def test_T064_score_contains_i7_projection():
    ontology = build_ontology(discover_pytest_tests())
    score = score_from_ontology(ontology)
    assert "v32_projected" in score["score"]


def test_T065_certification_power_has_near_term_ceiling():
    assert INSTRUMENTS["I7"]["near"] >= 92.0


def test_T066_risk_transparency_bias_security_runtime_are_named():
    target = INSTRUMENTS["I7"]["target"]
    for word in ["certification", "risk", "transparency", "bias", "security", "runtime", "auditability"]:
        assert word in target


def test_T067_public_number_requires_test_mapping():
    ontology = build_ontology(discover_pytest_tests())
    score = score_from_ontology(ontology)
    assert not any(g["name"] == "Unmapped tests" for g in score["gaps"])


def test_T068_scorecard_is_machine_readable():
    ontology = build_ontology(discover_pytest_tests())
    score = score_from_ontology(ontology)
    assert score["schema"] == "axiolev.ns.score_from_ontology/v1"


def test_T069_certification_power_not_static_only():
    ontology = build_ontology(discover_pytest_tests())
    assert ontology["instrument_totals"].get("I7", 0) >= 20
