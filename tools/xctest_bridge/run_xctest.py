"""XCTest bridge — executes `swift test` and parses results into pytest.

Closes Ring-5 gap #1: Mac UI/runtime layer becomes a measured gate
inside the pytest suite, not a manifest stub.
"""
from __future__ import annotations
import json
import re
import subprocess
import shutil
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO_ROOT / "apps" / "ns_mac"

_PASS_RE = re.compile(r"Test Case '-\[(\S+) (\S+)\]' passed")
_FAIL_RE = re.compile(r"Test Case '-\[(\S+) (\S+)\]' failed")
_SUITE_RE = re.compile(r"Test Suite '(\S+)' (passed|failed) at")


@dataclass
class XCTestResult:
    passed: int = 0
    failed: int = 0
    suites: List[str] = field(default_factory=list)
    failures: List[str] = field(default_factory=list)
    raw_output: str = ""
    swift_available: bool = True
    package_exists: bool = True

    @property
    def total(self) -> int:
        return self.passed + self.failed

    @property
    def ok(self) -> bool:
        return (self.swift_available
                and self.package_exists
                and self.failed == 0
                and self.passed >= 5)


def run_xctest(timeout: int = 300) -> XCTestResult:
    if shutil.which("swift") is None:
        return XCTestResult(swift_available=False, raw_output="swift not on PATH")
    if not (PACKAGE_DIR / "Package.swift").exists():
        return XCTestResult(package_exists=False,
                            raw_output=f"no Package.swift at {PACKAGE_DIR}")
    try:
        proc = subprocess.run(
            ["swift", "test"],
            cwd=str(PACKAGE_DIR),
            capture_output=True, text=True, timeout=timeout,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired as e:
        return XCTestResult(raw_output=f"timeout after {timeout}s: {e}")
    except Exception as e:
        return XCTestResult(raw_output=f"exec error: {e}")

    result = XCTestResult(raw_output=out[-4000:])
    for cls, name in _PASS_RE.findall(out):
        result.passed += 1
    for cls, name in _FAIL_RE.findall(out):
        result.failed += 1
        result.failures.append(f"{cls}.{name}")
    for suite, _ in _SUITE_RE.findall(out):
        if suite not in result.suites:
            result.suites.append(suite)
    return result


def write_report(out_dir: Path) -> XCTestResult:
    result = run_xctest()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "XCTEST_REPORT.json").write_text(
        json.dumps(asdict(result), indent=2, default=str)
    )
    return result


if __name__ == "__main__":
    import sys
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / ".run" / "xctest_latest"
    r = write_report(out)
    print(f"passed={r.passed} failed={r.failed} ok={r.ok}")
    print(f"report: {out / 'XCTEST_REPORT.json'}")
    sys.exit(0 if r.ok else 1)
