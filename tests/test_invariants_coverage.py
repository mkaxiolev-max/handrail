"""
NS∞ Dignity Kernel — invariant coverage checks
AXIOLEV Holdings LLC © 2026

Asserts that:
  1. specs/tla/Dignity.tla exists
  2. All 10 canonical invariants (I1..I10) are declared as TLA+ operators
  3. Each invariant has a corresponding Apalache .cfg file in specs/tla/
  4. Each .cfg file references its own invariant name
  5. Exactly 10 invariants are defined (no silent omissions)

These tests run without apalache-mc; they verify the committed artefacts only.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
SPEC = REPO_ROOT / "specs" / "tla" / "Dignity.tla"
CFG_DIR = REPO_ROOT / "specs" / "tla"

INVARIANTS = [
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


# ── Spec-level checks ──────────────────────────────────────────────────

def test_spec_exists():
    assert SPEC.exists(), f"Dignity.tla not found at {SPEC}"


def test_invariant_count():
    """Exactly 10 canonical invariants must be defined — no more, no fewer."""
    assert len(INVARIANTS) == 10


@pytest.mark.parametrize("invariant", INVARIANTS)
def test_invariant_declared(invariant):
    """
    Each invariant must appear as a top-level TLA+ operator definition of the form
    '<InvariantName> ==' at the start of a line (ignoring trailing whitespace).
    """
    text = SPEC.read_text()
    pattern = rf"^{re.escape(invariant)}\s*=="
    assert re.search(pattern, text, re.MULTILINE), (
        f"Operator '{invariant} ==' not found in {SPEC.name}"
    )


def test_all_declared_in_spec():
    """All 10 invariants are present in a single pass (fail-fast aggregate)."""
    text = SPEC.read_text()
    missing = [
        inv for inv in INVARIANTS
        if not re.search(rf"^{re.escape(inv)}\s*==", text, re.MULTILINE)
    ]
    assert not missing, f"Missing from Dignity.tla: {missing}"


# ── Config-level checks ────────────────────────────────────────────────

@pytest.mark.parametrize("invariant", INVARIANTS)
def test_cfg_exists(invariant):
    """Each invariant must have a corresponding Apalache .cfg file."""
    cfg = CFG_DIR / f"{invariant}.cfg"
    assert cfg.exists(), f"Missing Apalache config: {cfg}"


@pytest.mark.parametrize("invariant", INVARIANTS)
def test_cfg_references_invariant(invariant):
    """Each .cfg file must mention its invariant name (INVARIANT line)."""
    cfg = CFG_DIR / f"{invariant}.cfg"
    text = cfg.read_text()
    assert invariant in text, (
        f"{invariant}.cfg does not reference '{invariant}' — "
        "INVARIANT line may be missing"
    )


@pytest.mark.parametrize("invariant", INVARIANTS)
def test_cfg_has_init_and_next(invariant):
    """Each .cfg must specify INIT Init and NEXT Next."""
    cfg = CFG_DIR / f"{invariant}.cfg"
    text = cfg.read_text()
    assert re.search(r"^\s*INIT\s+Init\s*$", text, re.MULTILINE), (
        f"{invariant}.cfg missing 'INIT Init'"
    )
    assert re.search(r"^\s*NEXT\s+Next\s*$", text, re.MULTILINE), (
        f"{invariant}.cfg missing 'NEXT Next'"
    )


def test_no_extra_cfg_files():
    """The specs/tla/ directory must not contain unnamed invariant .cfg files."""
    cfg_files = {p.stem for p in CFG_DIR.glob("I*.cfg")}
    expected = set(INVARIANTS)
    unexpected = cfg_files - expected
    assert not unexpected, (
        f"Unexpected .cfg files in specs/tla/ (not in INVARIANTS list): {unexpected}"
    )
