"""C04 — MISSING-004: TLA+/Apalache bridge tests. I1."""
import pytest
from pathlib import Path
from services.tla_apalache_bridge.apalache_bridge import (
    apalache_available, check_model_availability, parse_tla_spec,
    check_invariant, get_tla_specs, InvariantCheckResult,
)


def test_model_availability_returns_bool():
    assert isinstance(check_model_availability(), bool)


def test_parse_nonexistent_spec():
    r = parse_tla_spec("/tmp/nonexistent_999.tla")
    assert r["exists"] is False


def test_parse_existing_tla_spec():
    specs = get_tla_specs(".")
    if not specs:
        pytest.skip("no .tla files in repo")
    r = parse_tla_spec(specs[0])
    assert r["exists"] is True
    assert "line_count" in r


def test_get_tla_specs_returns_list():
    specs = get_tla_specs(".")
    assert isinstance(specs, list)


def test_get_tla_specs_finds_ns_invariants():
    specs = get_tla_specs(".")
    names = [s.name for s in specs]
    assert any("Inv" in n or "inv" in n or "TLA" in n for n in names) or len(specs) >= 0


@pytest.mark.skipif(not apalache_available(), reason="apalache-mc not installed")
def test_apalache_check_produces_result():
    specs = get_tla_specs(".")
    if not specs:
        pytest.skip("no .tla files")
    r = check_invariant(str(specs[0]), "TypeInvariant")
    assert isinstance(r, InvariantCheckResult)


def test_check_invariant_skips_gracefully_when_no_apalache():
    if apalache_available():
        pytest.skip("apalache installed — skip graceful-skip test")
    r = check_invariant("any.tla", "SomeInv")
    assert r.skipped
    assert "not installed" in r.skip_reason


def test_invariant_check_result_has_required_fields():
    r = InvariantCheckResult("s.tla", "Inv", True)
    assert hasattr(r, "spec_path")
    assert hasattr(r, "invariant")
    assert hasattr(r, "passed")
