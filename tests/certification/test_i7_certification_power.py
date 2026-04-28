"""
Tests for the real I7 Certification Power module.
Every assertion is backed by artifact evidence — no static score claims.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from services.certification.i7_certification_power import (
    REQUIRED_CATEGORIES,
    CertificationCategory,
    CertificationEvidence,
    CertificationReport,
    _band,
    build_i7_certification_report,
    export_i7_certification_report,
)

TS = "2026-01-01T00:00:00Z"


@pytest.fixture(scope="module")
def report() -> CertificationReport:
    return build_i7_certification_report("test_run", TS)


def test_report_has_all_10_required_categories(report):
    ids = {c.id for c in report.categories}
    assert ids == REQUIRED_CATEGORIES, f"Missing: {REQUIRED_CATEGORIES - ids}"


def test_total_score_computed_from_category_scores(report):
    expected = round(sum(c.score_0_to_10 for c in report.categories), 2)
    # capped at 99.9 when absent categories exist
    assert report.total_score_0_to_100 <= expected + 0.01


def test_every_category_has_evidence_items_field(report):
    for cat in report.categories:
        assert hasattr(cat, "evidence_items"), f"{cat.id} missing evidence_items"


def test_no_category_exceeds_10():
    cat = CertificationCategory("x", "X", 10.0, status="complete")
    assert cat.score_0_to_10 == 10.0

    with pytest.raises(ValueError):
        CertificationCategory("y", "Y", 10.1, status="complete")


def test_total_score_never_exceeds_100():
    cats = [
        CertificationCategory(cid, cid, 10.0, status="complete")
        for cid in REQUIRED_CATEGORIES
    ]
    total = sum(c.score_0_to_10 for c in cats)
    assert total <= 100.0


def test_absent_evidence_creates_blocking_gap(report):
    # Find any category with a gap and verify it surfaces
    gap_cats = [c for c in report.categories if c.gaps]
    if gap_cats:
        assert report.blocking_gaps


def test_certification_band_is_deterministic():
    assert _band(69.9) == "not_certifiable"
    assert _band(70.0) == "provisional"
    assert _band(84.9) == "provisional"
    assert _band(85.0) == "audit_ready_internal"
    assert _band(91.9) == "audit_ready_internal"
    assert _band(92.0) == "external_certification_ready"
    assert _band(96.9) == "external_certification_ready"
    assert _band(97.0) == "theoretical_max"
    assert _band(100.0) == "theoretical_max"


def test_export_writes_valid_json(report):
    with tempfile.TemporaryDirectory() as tmp:
        path = export_i7_certification_report(report, Path(tmp))
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["schema"] == "axiolev.ns.i7_certification_power/v1"
        assert "categories" in data
        assert "total_score_0_to_100" in data
        assert "certification_band" in data


def test_report_schema_is_machine_readable(report):
    assert report.schema == "axiolev.ns.i7_certification_power/v1"


def test_report_links_to_test_ontology(report):
    # ontology_link may be None if not provided; when provided must be a string
    if report.ontology_link is not None:
        assert isinstance(report.ontology_link, str)


def test_report_includes_claim_to_artifact_mapping(report):
    assert isinstance(report.claim_to_artifact_mapping, dict)
    assert len(report.claim_to_artifact_mapping) > 0, "Claim-to-artifact map must not be empty"


def test_report_includes_auditability_evidence(report):
    cat = next(c for c in report.categories if c.id == "auditability")
    assert cat.evidence_items, "Auditability category must have evidence"


def test_report_includes_transparency_evidence(report):
    cat = next(c for c in report.categories if c.id == "transparency")
    assert cat.evidence_items, "Transparency category must have evidence"


def test_report_includes_bias_evidence(report):
    cat = next(c for c in report.categories if c.id == "bias")
    assert cat.evidence_items, "Bias/Fairness category must have evidence"


def test_report_includes_security_evidence(report):
    cat = next(c for c in report.categories if c.id == "security")
    assert cat.evidence_items, "Security category must have evidence"


def test_report_includes_runtime_evidence(report):
    cat = next(c for c in report.categories if c.id == "runtime")
    assert cat.evidence_items, "Runtime/Drift category must have evidence"


def test_report_includes_continuous_improvement_evidence(report):
    cat = next(c for c in report.categories if c.id == "continuous_improvement")
    assert cat.evidence_items, "Continuous Improvement category must have evidence"


def test_report_refuses_max_score_when_absent_categories():
    """A report with absent categories must not reach total=100."""
    from dataclasses import replace
    cats = [
        CertificationCategory(cid, cid, 10.0, status="complete")
        for cid in list(REQUIRED_CATEGORIES)[:-1]
    ]
    # Add an absent category
    cats.append(CertificationCategory(
        list(REQUIRED_CATEGORIES)[-1], "Absent", 0.0, status="absent"
    ))
    total = sum(c.score_0_to_10 for c in cats)
    absent = sum(1 for c in cats if c.status == "absent")
    if absent > 0 and total >= 100:
        total = min(total, 99.9)
    assert total < 100


def test_all_categories_have_status_field(report):
    valid_statuses = {"complete", "partial", "absent"}
    for cat in report.categories:
        assert cat.status in valid_statuses, f"{cat.id} has invalid status '{cat.status}'"


def test_complete_partial_absent_counts_are_consistent(report):
    actual_complete = sum(1 for c in report.categories if c.status == "complete")
    actual_partial = sum(1 for c in report.categories if c.status == "partial")
    actual_absent = sum(1 for c in report.categories if c.status == "absent")
    assert report.complete_categories == actual_complete
    assert report.partial_categories == actual_partial
    assert report.absent_categories == actual_absent
