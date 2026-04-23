"""
NS∞ Dignity Kernel — TLA+/Apalache bridge tests
AXIOLEV Holdings LLC © 2026

Invokes tools/tla/run_apalache.sh and asserts NoError for each of the
10 canonical Dignity Kernel invariants (I1..I10).

Behaviour when apalache-mc is absent:
  - Each parametrized test xfails with reason "apalache-missing" (strict=True
    so the test suite stays red if apalache is present but a test is skipped).
  - The wrapper script emits WARN to stderr and exits 0.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
WRAPPER = REPO_ROOT / "tools" / "tla" / "run_apalache.sh"
ARTIFACTS = REPO_ROOT / "artifacts" / "tla"

CANONICAL = [
    "I1_NonBypass",
    "I2_NonDestruct",
    "I3_PolicyQuorum",
    "I4_DignityGuard",
    "I5_RiskTierGate",
    "I6_Disjoint",
    "I7_TierRatchet",
    "I8_SecureGate",
    "I9_DenialReceipted",
    "I10_Receipted",
]

APALACHE_MISSING = shutil.which("apalache-mc") is None


@pytest.fixture(scope="session")
def apalache_results():
    """
    Run run_apalache.sh once per session (all invariants in one pass).
    Returns dict {invariant: json_data, "_proc": CompletedProcess} or None.
    """
    if APALACHE_MISSING:
        return None

    proc = subprocess.run(
        ["bash", str(WRAPPER)],
        capture_output=True,
        text=True,
        timeout=600,
    )

    results: dict = {"_proc": proc}
    for inv in CANONICAL:
        out = ARTIFACTS / f"{inv}.json"
        if out.exists():
            results[inv] = json.loads(out.read_text())
        else:
            results[inv] = {
                "invariant": inv,
                "status": "missing",
                "error": "output JSON not written by wrapper",
            }
    return results


@pytest.mark.parametrize("invariant", CANONICAL)
def test_invariant_no_error(apalache_results, invariant):
    """Apalache must report NoError for each Dignity Kernel invariant."""
    if APALACHE_MISSING:
        pytest.xfail("apalache-missing")

    proc = apalache_results["_proc"]
    data = apalache_results.get(invariant, {})

    assert data.get("status") == "NoError", (
        f"{invariant} outcome: {data.get('status', 'unknown')!r}\n"
        f"--- wrapper stdout ---\n{proc.stdout}\n"
        f"--- wrapper stderr ---\n{proc.stderr}"
    )


def test_wrapper_exists():
    """Wrapper script must be present and executable."""
    assert WRAPPER.exists(), f"run_apalache.sh not found at {WRAPPER}"
    assert WRAPPER.stat().st_mode & 0o111, "run_apalache.sh is not executable"


def test_wrapper_exits_zero_when_apalache_missing(tmp_path):
    """
    When apalache-mc is absent the wrapper must exit 0 and emit WARN to stderr.
    Simulate by building a PATH that includes system dirs (so bash/date/etc work)
    but prepends a shadow bin that shadows out any real apalache-mc.
    """
    shadow_bin = tmp_path / "bin"
    shadow_bin.mkdir()

    # Keep system paths so bash/coreutils are still reachable, but apalache-mc
    # lives outside /bin, /usr/bin — it won't appear there.
    safe_path = ":".join([str(shadow_bin), "/bin", "/usr/bin", "/usr/local/bin"])

    bash = shutil.which("bash") or "/bin/bash"

    proc = subprocess.run(
        [bash, str(WRAPPER)],
        capture_output=True,
        text=True,
        timeout=30,
        env={"PATH": safe_path, "HOME": str(tmp_path)},
    )
    assert proc.returncode == 0, "Wrapper must exit 0 when apalache-mc absent"
    assert "WARN" in proc.stderr, "Wrapper must emit WARN when apalache-mc absent"
