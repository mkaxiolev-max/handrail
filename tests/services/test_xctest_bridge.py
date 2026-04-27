"""XCTest bridge integration — Ring-5 #1 gate inside pytest suite. I7."""
from __future__ import annotations
import shutil
import pytest
from tools.xctest_bridge.run_xctest import run_xctest, XCTestResult


def test_bridge_module_importable():
    assert callable(run_xctest)


def test_xctest_runs_and_reports_clean():
    if shutil.which("swift") is None:
        pytest.skip("swift not on PATH")
    r = run_xctest(timeout=180)
    assert isinstance(r, XCTestResult)
    assert r.swift_available, "swift binary missing"
    assert r.package_exists, "apps/ns_mac/Package.swift missing"
    assert r.failed == 0, f"XCTest failures: {r.failures}\n{r.raw_output}"
    assert r.passed >= 5, (
        f"expected >=5 XCTest cases passing, got {r.passed}\n{r.raw_output}"
    )


def test_xctest_covers_five_required_components():
    if shutil.which("swift") is None:
        pytest.skip("swift not on PATH")
    r = run_xctest(timeout=180)
    required = {
        "FounderHome", "LivingArchitecture",
        "VoicePanel", "ScoreHistory", "KeyboardHandler",
    }
    out = r.raw_output
    for name in required:
        assert name in out, f"component {name} not covered in XCTest run"


def test_xctest_result_has_ok_property():
    r = XCTestResult(passed=5, failed=0)
    assert r.ok is True
    r2 = XCTestResult(passed=5, failed=1)
    assert r2.ok is False
