"""Tests for the Validator adapter framework — AXIOLEV Holdings LLC © 2026.

Coverage:
  - Protocol conformance for all three adapters
  - Dispatch table routing (registry)
  - Golden-result fixtures per adapter
  - Receipt emission and Lineage Fabric chain integrity
  - I3 admin cap enforcement (confidence ≤ 0.95)
  - ValidationResult schema completeness
"""
import pytest
from services.validators.contracts import (
    ValidationResult, ValidatorAdapter, I3_ADMIN_CAP, cap_confidence,
    emit_lineage_receipt, _LINEAGE_STATE,
)
from services.validators.lean_math import LeanMathAdapter
from services.validators.dft_physics_stub import DFTPhysicsAdapter
from services.validators.fda_biomed import FDABiomedAdapter
from services.validators.registry import dispatch, registered_domains
from services.validators import (
    LeanMathAdapter as LeanImport,
    DFTPhysicsAdapter as DFTImport,
    FDABiomedAdapter as FDAImport,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def lean(): return LeanMathAdapter()

@pytest.fixture
def dft(): return DFTPhysicsAdapter()

@pytest.fixture
def fda(): return FDABiomedAdapter()


# ---------------------------------------------------------------------------
# 1. Protocol conformance
# ---------------------------------------------------------------------------

def test_lean_math_protocol(lean):
    assert lean.domain == "math"
    assert callable(lean.validate)

def test_dft_physics_protocol(dft):
    assert dft.domain == "physics"
    assert callable(dft.validate)

def test_fda_biomed_protocol(fda):
    assert fda.domain == "biomedical"
    assert callable(fda.validate)

def test_package_re_exports_adapters():
    # __init__.py must re-export all three
    assert LeanImport is LeanMathAdapter
    assert DFTImport  is DFTPhysicsAdapter
    assert FDAImport  is FDABiomedAdapter


# ---------------------------------------------------------------------------
# 2. Dispatch table
# ---------------------------------------------------------------------------

def test_dispatch_math():
    r = dispatch("math", "1 = 1", {})
    assert r.domain == "math"
    assert r.adapter == "lean_math"

def test_dispatch_physics():
    r = dispatch("physics", "band gap of Si is 1.1 eV", {
        "quantity": "band_gap_ev", "value": 1.1, "converged": True,
    })
    assert r.domain == "physics"
    assert r.adapter == "dft_physics_stub"

def test_dispatch_biomedical():
    r = dispatch("biomedical", "aspirin 100 mg/day", {"evidence_tier": "T2"})
    assert r.domain == "biomedical"
    assert r.adapter == "fda_biomed"

def test_dispatch_alias_materials():
    r = dispatch("materials", "Si band gap 1.1 eV", {
        "quantity": "band_gap_ev", "value": 1.1,
    })
    assert r.adapter == "dft_physics_stub"

def test_dispatch_alias_clinical():
    r = dispatch("clinical", "aspirin 100 mg/day", {"evidence_tier": "T2"})
    assert r.adapter == "fda_biomed"

def test_dispatch_unknown_domain():
    r = dispatch("alchemy", "lead → gold", {})
    assert r.verdict == "UNSUPPORTED"
    assert r.confidence == 0.0
    assert "alchemy" in r.rationale

def test_registered_domains_content():
    domains = registered_domains()
    assert "math"       in domains
    assert "physics"    in domains
    assert "biomedical" in domains


# ---------------------------------------------------------------------------
# 3. I3 admin cap enforcement (confidence ≤ 0.95)
# ---------------------------------------------------------------------------

def test_lean_math_confidence_cap(lean):
    r = lean.validate("1 = 1", {})
    assert r.confidence <= I3_ADMIN_CAP

def test_dft_physics_confidence_cap(dft):
    r = dft.validate("band gap", {"quantity": "band_gap_ev", "value": 1.1, "converged": True})
    assert r.confidence <= I3_ADMIN_CAP

def test_fda_biomed_confidence_cap(fda):
    r = fda.validate("aspirin 100 mg/day reduces fever", {
        "evidence_tier": "T1", "p_value": 0.001, "effect_size": 0.4,
    })
    assert r.confidence <= I3_ADMIN_CAP

def test_cap_confidence_clamps():
    assert cap_confidence(0.99) == pytest.approx(I3_ADMIN_CAP)
    assert cap_confidence(0.50) == pytest.approx(0.50)
    assert cap_confidence(0.95) == pytest.approx(0.95)


# ---------------------------------------------------------------------------
# 4. Receipt emission and Lineage Fabric chain integrity
# ---------------------------------------------------------------------------

def test_receipt_id_nonempty(lean):
    r = lean.validate("2 = 2", {"claim_id": "cid_receipt_test"})
    assert isinstance(r.receipt_id, str)
    assert len(r.receipt_id) > 0

def test_lineage_hash_nonempty(lean):
    r = lean.validate("3 = 3", {})
    assert isinstance(r.lineage_hash, str)
    assert len(r.lineage_hash) == 64  # SHA-256 hex digest

def test_lineage_chain_progresses(lean):
    h1 = _LINEAGE_STATE["prev_hash"]
    lean.validate("4 = 4", {})
    h2 = _LINEAGE_STATE["prev_hash"]
    lean.validate("5 = 5", {})
    h3 = _LINEAGE_STATE["prev_hash"]
    assert h1 != h2
    assert h2 != h3

def test_lineage_receipt_buffered():
    before = len(_LINEAGE_STATE["receipts"])
    emit_lineage_receipt("cid_buf", "test", "test_adapter", "PASS", 0.5, {})
    assert len(_LINEAGE_STATE["receipts"]) == before + 1

def test_all_receipts_have_required_keys():
    emit_lineage_receipt("cid_keys", "test", "test_adapter", "UNCERTAIN", 0.4, {"x": 1})
    last = _LINEAGE_STATE["receipts"][-1]
    for key in ("receipt_id", "prev_hash", "claim_id", "domain", "adapter",
                "verdict", "confidence", "ts_utc", "lineage_hash"):
        assert key in last, f"missing key: {key}"


# ---------------------------------------------------------------------------
# 5. ValidationResult schema completeness
# ---------------------------------------------------------------------------

def test_result_schema_complete(lean):
    r = lean.validate("1 = 1", {"claim_id": "schema_test"})
    assert isinstance(r, ValidationResult)
    assert r.claim_id == "schema_test"
    assert r.domain   == "math"
    assert r.adapter  == "lean_math"
    assert r.verdict  in ("PASS", "FAIL", "UNCERTAIN", "UNSUPPORTED")
    assert 0.0 <= r.confidence <= 1.0
    assert isinstance(r.rationale, str) and len(r.rationale) > 0
    assert isinstance(r.checks, dict)
    assert isinstance(r.receipt_id, str)
    assert isinstance(r.lineage_hash, str)
    assert r.ts > 0

def test_result_to_json_round_trip(lean):
    r = lean.validate("6 = 6", {})
    import json
    d = json.loads(r.to_json())
    assert d["verdict"]  == r.verdict
    assert d["claim_id"] == r.claim_id
    assert d["adapter"]  == r.adapter


# ---------------------------------------------------------------------------
# 6. LeanMathAdapter golden-result fixtures
# ---------------------------------------------------------------------------

def test_lean_numeric_true(lean):
    r = lean.validate("1 = 1", {})
    assert r.verdict == "PASS"
    assert r.confidence == pytest.approx(0.88)

def test_lean_numeric_false(lean):
    r = lean.validate("1 = 2", {})
    assert r.verdict == "FAIL"
    assert r.confidence == pytest.approx(0.88)

def test_lean_numeric_comparison_pass(lean):
    r = lean.validate("3 > 2", {})
    assert r.verdict == "PASS"

def test_lean_unbalanced_brackets(lean):
    r = lean.validate("(1 + 2", {})
    assert r.verdict == "FAIL"
    assert "bracket" in r.rationale.lower()

def test_lean_known_identity_pythagoras(lean):
    r = lean.validate("a^2 + b^2 = c^2", {"identity_key": "pythagoras"})
    assert r.verdict == "PASS"
    assert r.confidence == pytest.approx(0.80)

def test_lean_unknown_symbolic_uncertain(lean):
    # Non-numeric, no identity key, no Lean binary expected in test env
    r = lean.validate("x^2 + y^2 = z^2", {})
    assert r.verdict in ("UNCERTAIN", "FAIL", "PASS")  # Lean may or may not be present
    assert r.confidence <= I3_ADMIN_CAP


# ---------------------------------------------------------------------------
# 7. DFTPhysicsAdapter golden-result fixtures
# ---------------------------------------------------------------------------

def test_dft_band_gap_in_range_converged(dft):
    r = dft.validate("Si band gap", {
        "quantity": "band_gap_ev", "value": 1.1, "converged": True,
    })
    assert r.verdict == "PASS"
    assert r.confidence == pytest.approx(0.70)

def test_dft_band_gap_out_of_range(dft):
    r = dft.validate("fictional material", {
        "quantity": "band_gap_ev", "value": 100.0,
    })
    assert r.verdict == "FAIL"
    assert "outside" in r.rationale.lower()

def test_dft_convergence_false(dft):
    r = dft.validate("converged?", {
        "quantity": "lattice_constant_A", "value": 5.43, "converged": False,
    })
    assert r.verdict == "FAIL"
    assert "convergence" in r.rationale.lower()

def test_dft_no_context_uncertain(dft):
    r = dft.validate("some material property claim", {})
    assert r.verdict == "UNCERTAIN"
    assert r.confidence <= I3_ADMIN_CAP

def test_dft_unknown_quantity_uncertain(dft):
    r = dft.validate("entropy claim", {"quantity": "entropy_JK", "value": 100.0})
    assert r.verdict == "UNCERTAIN"


# ---------------------------------------------------------------------------
# 8. FDABiomedAdapter golden-result fixtures
# ---------------------------------------------------------------------------

def test_fda_t1_pass(fda):
    r = fda.validate("Drug X reduces hypertension by 10 mmHg", {
        "evidence_tier": "T1", "p_value": 0.001, "effect_size": 0.3,
        "claim_id": "fda_t1_pass",
    })
    assert r.verdict == "PASS"
    assert r.confidence == pytest.approx(I3_ADMIN_CAP)

def test_fda_no_evidence_unsupported(fda):
    r = fda.validate("Drug X cures everything", {})
    assert r.verdict == "UNSUPPORTED"
    assert r.confidence == 0.0

def test_fda_contraindicated_fail(fda):
    r = fda.validate("Drug X is safe in pregnancy", {
        "evidence_tier": "T2", "contraindicated": True,
    })
    assert r.verdict == "FAIL"
    assert r.confidence == pytest.approx(0.92)

def test_fda_dosage_excess_fail(fda):
    r = fda.validate("Aspirin 5000 mg/day is effective", {
        "drug": "aspirin", "evidence_tier": "T2",
    })
    assert r.verdict == "FAIL"
    assert "5000" in r.rationale or "exceed" in r.rationale.lower()

def test_fda_dosage_within_limit_t2_uncertain(fda):
    r = fda.validate("Aspirin 500 mg/day reduces fever", {
        "drug": "aspirin", "evidence_tier": "T2",
    })
    assert r.verdict == "UNCERTAIN"
    assert r.confidence <= _fda_biomed_cap()

def test_fda_t4_weak_uncertain(fda):
    r = fda.validate("Compound X shows anti-tumour activity in cell line", {
        "evidence_tier": "T4",
    })
    assert r.verdict == "UNCERTAIN"
    assert r.confidence < 0.35


def _fda_biomed_cap() -> float:
    from services.validators.fda_biomed import _BIOMED_CAP
    return _BIOMED_CAP
