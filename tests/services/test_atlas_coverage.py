"""C13 — MISSING-009: MITRE ATLAS v5.4 coverage tests. I7."""
from services.atlas_coverage.atlas import ATLASCoverageMatrix, ATLAS_TACTICS


def test_atlas_has_15_tactics():
    assert len(ATLAS_TACTICS) == 15


def test_matrix_initializes():
    m = ATLASCoverageMatrix()
    assert m.tactic_count() == 15


def test_ns_mitigations_pre_populated():
    m = ATLASCoverageMatrix()
    assert m.coverage_pct() > 0


def test_add_mitigation():
    m = ATLASCoverageMatrix()
    m.add_mitigation("lateral-movement", "network_segmentation")
    assert "lateral-movement" not in m.uncovered_tactics()


def test_coverage_pct_increases_after_adding():
    m = ATLASCoverageMatrix()
    before = m.coverage_pct()
    for tactic in m.uncovered_tactics():
        m.add_mitigation(tactic, "test_mitigation")
    assert m.coverage_pct() >= before


def test_full_coverage_is_100():
    m = ATLASCoverageMatrix()
    for t in ATLAS_TACTICS:
        m.add_mitigation(t, "mitigation")
    assert m.coverage_pct() == 100.0


def test_unknown_tactic_raises():
    import pytest
    m = ATLASCoverageMatrix()
    with pytest.raises(ValueError):
        m.add_mitigation("invented_tactic_xyz", "x")
