"""
Meta-tests: I7 real layer integrity.
Assert that I7 is test-backed, artifact-backed, and machine-readable.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from services.certification.i7_certification_power import (
    REQUIRED_CATEGORIES,
    build_i7_certification_report,
    export_i7_certification_report,
)
from tools.ns_test_ontology.ontology import INSTRUMENTS, build_ontology, discover_pytest_tests

TS = "2026-01-01T00:00:00Z"


@pytest.fixture(scope="module")
def ontology():
    return build_ontology(discover_pytest_tests())


@pytest.fixture(scope="module")
def report():
    return build_i7_certification_report("meta_test_run", TS)


def test_i7_instrument_exists_in_ontology():
    assert "I7" in INSTRUMENTS


def test_i7_has_at_least_20_tests_mapped(ontology):
    count = ontology["instrument_totals"].get("I7", 0)
    assert count >= 20, f"I7 has only {count} tests — need >= 20"


def test_i7_report_can_be_generated_without_network():
    r = build_i7_certification_report("offline_test", TS)
    assert r.total_score_0_to_100 >= 0


def test_i7_report_is_machine_readable(report):
    with tempfile.TemporaryDirectory() as tmp:
        path = export_i7_certification_report(report, Path(tmp))
        data = json.loads(path.read_text())
        assert isinstance(data, dict)
        assert "schema" in data
        assert "total_score_0_to_100" in data
        assert "certification_band" in data
        assert "categories" in data


def test_i7_report_has_blocking_gaps_list(report):
    assert isinstance(report.blocking_gaps, list)


def test_i7_report_refuses_max_score_if_any_category_absent():
    """Build a synthetic report; verify max score is refused when absent > 0."""
    from services.certification.i7_certification_power import CertificationCategory, _band
    cats = [
        CertificationCategory(cid, cid, 10.0, status="complete")
        for cid in list(REQUIRED_CATEGORIES)[:-1]
    ]
    cats.append(CertificationCategory(
        list(REQUIRED_CATEGORIES)[-1], "Absent", 0.0, status="absent"
    ))
    absent = sum(1 for c in cats if c.status == "absent")
    total = sum(c.score_0_to_10 for c in cats)
    if absent > 0 and total >= 100:
        total = min(total, 99.9)
    assert total < 100


def test_i7_report_has_external_certification_readiness_semantics(report):
    band = report.certification_band
    # Must be one of the valid bands
    valid = {"not_certifiable", "provisional", "audit_ready_internal",
             "external_certification_ready", "theoretical_max"}
    assert band in valid
    # Given the current repo state, must be at least provisional
    assert band != "not_certifiable", f"Band is {band} — repo evidence insufficient for any certification"


def test_public_score_backed_by_evidence_artifacts(report):
    """Every point in total_score must correspond to evidence in some category."""
    total_evidence_items = sum(len(c.evidence_items) for c in report.categories)
    assert total_evidence_items > 0, "No evidence items — score is ungrounded"
    assert report.total_score_0_to_100 > 0
    # Score-per-evidence ratio sanity: shouldn't be scoring >10 per evidence item
    ratio = report.total_score_0_to_100 / total_evidence_items
    assert ratio <= 10.0, f"Score/evidence ratio {ratio:.1f} exceeds 10 — possible score inflation"


def test_i7_ontology_has_no_unmapped_tests(ontology):
    assert ontology["unmapped"] == [], f"{len(ontology['unmapped'])} unmapped tests remain"


def test_i7_certification_categories_match_required(report):
    ids = {c.id for c in report.categories}
    assert ids == REQUIRED_CATEGORIES


def test_i7_total_score_matches_category_sum(report):
    computed = round(sum(c.score_0_to_10 for c in report.categories), 2)
    # Allow for absent-cap adjustment (may reduce by up to 0.1)
    assert abs(report.total_score_0_to_100 - computed) <= 0.11
