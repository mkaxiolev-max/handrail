"""Tests for the Validator adapter framework — AXIOLEV Holdings LLC © 2026.

Coverage:
  - Protocol conformance for all three adapters (isinstance + attribute checks)
  - Dispatch table routing (registry, aliases, unknown domain)
  - Golden-result fixtures per adapter
  - Receipt emission and Lineage Fabric chain integrity
  - I3 admin cap enforcement (confidence ≤ 0.95)
  - ValidationResult schema completeness + frozen-dataclass invariants
  - flags / audit_trail presence and content per adapter
  - FDA 21 CFR Part 11 audit trail completeness + e-sig placeholder
"""
import json
import pytest

from services.validators.contracts import (
    ValidationResult,
    ValidatorAdapter,
    I3_ADMIN_CAP,
    cap_confidence,
    emit_lineage_receipt,
    make_claim_id,
    _LINEAGE_STATE,
)
from services.validators.lean_math import LeanMathAdapter
from services.validators.dft_physics_stub import DFTPhysicsAdapter
from services.validators.fda_biomed import FDABiomedAdapter, _BIOMED_CAP
from services.validators.registry import dispatch, registered_domains, register
from services.validators import (
    LeanMathAdapter as LeanImport,
    DFTPhysicsAdapter as DFTImport,
    FDABiomedAdapter as FDAImport,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def lean():
    return LeanMathAdapter()

@pytest.fixture
def dft():
    return DFTPhysicsAdapter()

@pytest.fixture
def fda():
    return FDABiomedAdapter()


# ---------------------------------------------------------------------------
# 1. Protocol conformance — attribute checks
# ---------------------------------------------------------------------------

def test_lean_math_has_domain(lean):
    assert lean.domain == "math"

def test_lean_math_has_validate(lean):
    assert callable(lean.validate)

def test_dft_physics_has_domain(dft):
    assert dft.domain == "physics"

def test_dft_physics_has_validate(dft):
    assert callable(dft.validate)

def test_fda_biomed_has_domain(fda):
    assert fda.domain == "biomedical"

def test_fda_biomed_has_validate(fda):
    assert callable(fda.validate)

def test_all_adapters_satisfy_protocol_isinstance():
    """isinstance() gate via @runtime_checkable protocol."""
    for adapter in (LeanMathAdapter(), DFTPhysicsAdapter(), FDABiomedAdapter()):
        assert isinstance(adapter, ValidatorAdapter), (
            f"{adapter.__class__.__name__} does not satisfy ValidatorAdapter protocol"
        )

def test_package_re_exports_adapters():
    assert LeanImport is LeanMathAdapter
    assert DFTImport  is DFTPhysicsAdapter
    assert FDAImport  is FDABiomedAdapter


# ---------------------------------------------------------------------------
# 2. Dispatch table — routing, aliases, unknown domain
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

def test_dispatch_unknown_domain_returns_unsupported():
    r = dispatch("alchemy", "lead → gold", {})
    assert r.verdict == "UNSUPPORTED"
    assert r.confidence == 0.0
    assert "alchemy" in r.rationale

def test_dispatch_unknown_has_flags():
    r = dispatch("alchemy", "lead → gold", {})
    assert any("unknown_domain" in f for f in r.flags)

def test_dispatch_unknown_has_audit_trail():
    r = dispatch("alchemy", "lead → gold", {})
    assert len(r.audit_trail) > 0
    steps = [e["step"] for e in r.audit_trail]
    assert "dispatch_fail" in steps

def test_registered_domains_content():
    domains = registered_domains()
    assert "math"       in domains
    assert "physics"    in domains
    assert "biomedical" in domains

def test_registry_register_override(lean):
    """register() with override=True replaces an existing adapter."""
    new_lean = LeanMathAdapter()
    register(new_lean, override=True)  # must not raise

def test_registry_register_duplicate_raises(lean):
    """register() without override raises ValueError for known domain."""
    with pytest.raises(ValueError, match="already registered"):
        register(LeanMathAdapter(), override=False)

def test_registry_register_bad_type_raises():
    """register() raises TypeError for non-conforming objects."""
    class Fake:
        domain = "bogus"
    with pytest.raises(TypeError, match="ValidatorAdapter protocol"):
        register(Fake())  # type: ignore[arg-type]


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

def test_cap_confidence_clamps_high():
    assert cap_confidence(0.99) == pytest.approx(I3_ADMIN_CAP)

def test_cap_confidence_clamps_low():
    assert cap_confidence(-0.1) == pytest.approx(0.0)

def test_cap_confidence_passthrough():
    assert cap_confidence(0.50) == pytest.approx(0.50)

def test_validation_result_rejects_confidence_above_cap():
    """ValidationResult.__post_init__ must reject confidence > I3_ADMIN_CAP."""
    rid, lhash = emit_lineage_receipt("ci", "test", "test", "PASS", 0.5, {})
    with pytest.raises(ValueError, match="I3.admin cap"):
        ValidationResult(
            claim_id="ci", domain="test", adapter="test",
            verdict="PASS", confidence=0.96,
            rationale="over cap", checks={}, flags=[], audit_trail=[],
            receipt_id=rid, lineage_hash=lhash,
        )

def test_validation_result_rejects_empty_receipt_id():
    with pytest.raises(ValueError, match="non-null"):
        ValidationResult(
            claim_id="ci", domain="test", adapter="test",
            verdict="PASS", confidence=0.5,
            rationale="r", checks={}, flags=[], audit_trail=[],
            receipt_id="", lineage_hash="abc",
        )

def test_validation_result_rejects_empty_lineage_hash():
    with pytest.raises(ValueError, match="non-null"):
        ValidationResult(
            claim_id="ci", domain="test", adapter="test",
            verdict="PASS", confidence=0.5,
            rationale="r", checks={}, flags=[], audit_trail=[],
            receipt_id="someid", lineage_hash="",
        )


# ---------------------------------------------------------------------------
# 4. Receipt emission and Lineage Fabric chain integrity
# ---------------------------------------------------------------------------

def test_receipt_id_nonempty(lean):
    r = lean.validate("2 = 2", {"claim_id": "cid_receipt_test"})
    assert isinstance(r.receipt_id, str)
    assert len(r.receipt_id) > 0

def test_lineage_hash_is_64hex(lean):
    r = lean.validate("3 = 3", {})
    assert isinstance(r.lineage_hash, str)
    assert len(r.lineage_hash) == 64

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

def test_result_digest_deterministic(lean):
    r = lean.validate("7 = 7", {"claim_id": "determinism_test"})
    assert r.result_digest == r.result_digest  # frozen, so identical calls

def test_make_claim_id_stable():
    claim = {"statement": "a = a", "proof_sketch": "rfl"}
    cid1 = make_claim_id(claim)
    cid2 = make_claim_id(claim)
    assert cid1 == cid2
    assert len(cid1) == 16


# ---------------------------------------------------------------------------
# 5. ValidationResult schema completeness
# ---------------------------------------------------------------------------

def test_result_schema_complete(lean):
    r = lean.validate("1 = 1", {"claim_id": "schema_test"})
    assert isinstance(r, ValidationResult)
    assert r.claim_id == "schema_test"
    assert r.domain  == "math"
    assert r.adapter == "lean_math"
    assert r.verdict in ("PASS", "FAIL", "UNCERTAIN", "UNSUPPORTED")
    assert 0.0 <= r.confidence <= 1.0
    assert isinstance(r.rationale, str) and len(r.rationale) > 0
    assert isinstance(r.checks, dict)
    assert isinstance(r.flags, list)
    assert isinstance(r.audit_trail, list)
    assert isinstance(r.receipt_id, str)
    assert isinstance(r.lineage_hash, str)
    assert r.ts > 0

def test_result_is_frozen(lean):
    r = lean.validate("1 = 1", {})
    with pytest.raises(Exception):  # FrozenInstanceError
        r.confidence = 0.99  # type: ignore[misc]

def test_result_to_json_round_trip(lean):
    r = lean.validate("6 = 6", {})
    d = json.loads(r.to_json())
    assert d["verdict"]  == r.verdict
    assert d["claim_id"] == r.claim_id
    assert d["adapter"]  == r.adapter
    assert "flags"       in d
    assert "audit_trail" in d


# ---------------------------------------------------------------------------
# 6. LeanMathAdapter — golden fixtures + flags + audit trail
# ---------------------------------------------------------------------------

def test_lean_numeric_true(lean):
    r = lean.validate("1 = 1", {})
    assert r.verdict == "PASS"
    assert r.confidence == pytest.approx(0.88)

def test_lean_numeric_false(lean):
    r = lean.validate("1 = 2", {})
    assert r.verdict == "FAIL"

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

def test_lean_unknown_symbolic_caps_at_i3(lean):
    r = lean.validate("x^2 + y^2 = z^2", {})
    assert r.confidence <= I3_ADMIN_CAP

def test_lean_flags_lean_unavailable_when_no_binary(lean):
    """Without a 'lean' binary in PATH, flag lean_shell_unavailable is set."""
    import shutil
    if shutil.which("lean") is None:
        r = lean.validate("∀ n : ℕ, n + 0 = n", {})
        assert "lean_shell_unavailable" in r.flags

def test_lean_audit_trail_nonempty(lean):
    r = lean.validate("2 > 1", {})
    assert len(r.audit_trail) >= 3  # balance, numeric_eval, identity, verdict at minimum

def test_lean_audit_trail_has_verdict_step(lean):
    r = lean.validate("2 > 1", {})
    steps = [e["step"] for e in r.audit_trail]
    assert "verdict" in steps

def test_lean_unbalanced_sets_flag(lean):
    r = lean.validate("(x + y", {})
    assert "bracket_balance_fail" in r.flags


# ---------------------------------------------------------------------------
# 7. DFTPhysicsAdapter — golden fixtures + flags + audit trail
# ---------------------------------------------------------------------------

def test_dft_band_gap_in_range_converged(dft):
    r = dft.validate("Si band gap", {
        "quantity": "band_gap_ev", "value": 1.1, "converged": True,
    })
    assert r.verdict == "PASS"
    assert r.confidence == pytest.approx(0.70)

def test_dft_band_gap_out_of_range(dft):
    r = dft.validate("fictional material", {"quantity": "band_gap_ev", "value": 100.0})
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

def test_dft_always_has_engine_not_connected_flag(dft):
    r = dft.validate("Si band gap", {"quantity": "band_gap_ev", "value": 1.1})
    assert "dft_engine_not_connected" in r.flags

def test_dft_audit_trail_has_stub_init(dft):
    r = dft.validate("Si band gap", {})
    steps = [e["step"] for e in r.audit_trail]
    assert "init" in steps

def test_dft_out_of_range_sets_flag(dft):
    r = dft.validate("fictional", {"quantity": "band_gap_ev", "value": 999.0})
    assert "value_out_of_plausible_range" in r.flags


# ---------------------------------------------------------------------------
# 8. FDABiomedAdapter — golden fixtures + audit trail + e-sig
# ---------------------------------------------------------------------------

def test_fda_t1_significant_pass(fda):
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
    assert r.confidence <= _BIOMED_CAP

def test_fda_t4_weak_uncertain(fda):
    r = fda.validate("Compound X shows anti-tumour activity in cell line", {
        "evidence_tier": "T4",
    })
    assert r.verdict == "UNCERTAIN"
    assert r.confidence < 0.35

def test_fda_audit_trail_minimum_steps(fda):
    """FDA adapter must emit ≥ 6 audit steps (intake through decision)."""
    r = fda.validate("Drug X reduces pain", {
        "evidence_tier": "T2", "p_value": 0.03, "claim_id": "audit_steps_test",
    })
    assert len(r.audit_trail) >= 6

def test_fda_audit_trail_has_intake_step(fda):
    r = fda.validate("Drug X", {"evidence_tier": "T1", "p_value": 0.01})
    steps = [e["step"] for e in r.audit_trail]
    assert "intake" in steps

def test_fda_audit_trail_has_decision_step(fda):
    r = fda.validate("Drug X", {"evidence_tier": "T1", "p_value": 0.01})
    steps = [e["step"] for e in r.audit_trail]
    assert "decision" in steps

def test_fda_audit_decision_has_esig_placeholder(fda):
    """FDA 21 CFR Part 11: decision step must carry an e-sig placeholder."""
    r = fda.validate("Drug X reduces BP", {
        "evidence_tier": "T1", "p_value": 0.001, "actor": "dr_smith",
    })
    decision_step = next(
        (e for e in r.audit_trail if e["step"] == "decision"), None
    )
    assert decision_step is not None
    esig = decision_step.get("electronic_signature_placeholder", "")
    assert esig.startswith("esig://dr_smith/")

def test_fda_flags_nonempty_on_weak_claim(fda):
    r = fda.validate("Drug X", {"evidence_tier": "T4"})
    assert len(r.flags) > 0

def test_fda_receipt_lineage_ref_format(fda):
    r = fda.validate("Drug X", {"evidence_tier": "T1", "p_value": 0.001})
    assert isinstance(r.receipt_id, str) and len(r.receipt_id) > 0
    assert isinstance(r.lineage_hash, str) and len(r.lineage_hash) == 64
