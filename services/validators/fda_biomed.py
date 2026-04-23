"""FDA-class biomedical validator adapter — AXIOLEV Holdings LLC © 2026.

Regulatory-aware validation of biomedical claims with full audit trail.
Audit pattern follows FDA 21 CFR Part 11 intent; evidence hierarchy
follows ICH E6(R2) GCP tiers.

Evidence tiers (descending strength):
  T1 — Randomised controlled trial with statistical significance + effect size
  T2 — Observational / cohort / case-control study
  T3 — Case series or expert consensus opinion
  T4 — In-vitro / pre-clinical only
  (absent) — claim is UNSUPPORTED

Hard caps:
  _BIOMED_CAP (0.85) — ceiling without T1 evidence
  I3_ADMIN_CAP (0.95) — absolute ceiling per I3 constraint

Context keys recognised:
  claim_id       — str (auto-generated if absent)
  evidence_tier  — "T1" | "T2" | "T3" | "T4"
  drug           — str: drug name for dosage-limit lookup
  population     — str: patient population description
  indication     — str: clinical indication
  contraindicated — bool: caller-attested contraindication flag
  p_value        — float: reported p-value (T1 claims)
  effect_size    — float | str: reported effect size
"""
from __future__ import annotations
import re, uuid
from typing import Any, Dict

from .contracts import ValidationResult, Verdict, emit_lineage_receipt, cap_confidence

_BIOMED_CAP: float = 0.85   # non-T1 hard cap
_T1_CAP:     float = 0.95   # resolves to I3_ADMIN_CAP after cap_confidence()

_DOSAGE_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(mg|mcg|μg|g|IU|mL|L)(?:/(?:kg|m2|day|dose))?",
    re.IGNORECASE,
)

# Illustrative safe daily dose upper bounds (mg/day) for common reference drugs
_KNOWN_DOSAGE_LIMITS: Dict[str, float] = {
    "aspirin":       4000.0,
    "ibuprofen":     3200.0,
    "acetaminophen": 4000.0,
    "metformin":     2550.0,
}

_EVIDENCE_TIERS: Dict[str, int] = {"T1": 4, "T2": 3, "T3": 2, "T4": 1}


def _check_dosage(claim: str, context: Dict[str, Any]) -> Dict[str, Any]:
    drug = context.get("drug", "").lower()
    matches = _DOSAGE_RE.findall(claim)
    if not matches:
        return {"dosage_found": False}
    dosage_str, unit = matches[0]
    dosage_val = float(dosage_str)
    result: Dict[str, Any] = {
        "dosage_found": True, "value": dosage_val, "unit": unit, "drug": drug,
    }
    limit = _KNOWN_DOSAGE_LIMITS.get(drug)
    if limit and unit.lower() == "mg":
        result["within_known_limit"]   = dosage_val <= limit
        result["known_limit_mg_day"]   = limit
    return result


class FDABiomedAdapter:
    domain = "biomedical"

    def validate(self, claim: str, context: Dict[str, Any]) -> ValidationResult:
        claim_id = context.get("claim_id", uuid.uuid4().hex[:12])
        checks: Dict[str, Any] = {
            "regulatory_framework": "FDA 21 CFR Part 11 / ICH E6(R2)",
            "audit_trail": True,
        }

        tier_raw = str(context.get("evidence_tier", "")).upper()
        tier_score = _EVIDENCE_TIERS.get(tier_raw, 0)
        checks["evidence_tier"] = tier_raw or "UNSUPPORTED"
        checks["tier_score"]    = tier_score

        dosage_check = _check_dosage(claim, context)
        checks["dosage"] = dosage_check

        checks["population"]     = context.get("population", "")
        checks["indication"]     = context.get("indication", "")
        contraindicated          = context.get("contraindicated", False)
        checks["contraindicated"] = contraindicated

        p_value     = context.get("p_value")
        effect_size = context.get("effect_size")
        checks["p_value"]     = p_value
        checks["effect_size"] = effect_size

        if contraindicated:
            verdict: Verdict = "FAIL"
            confidence = cap_confidence(0.92)
            rationale = "Contraindication flag set — claim is clinically unsafe"

        elif dosage_check.get("within_known_limit") is False:
            verdict = "FAIL"
            confidence = cap_confidence(0.88)
            rationale = (
                f"Dosage {dosage_check['value']} {dosage_check['unit']} exceeds "
                f"known safe limit {dosage_check.get('known_limit_mg_day')} mg/day "
                f"for {dosage_check.get('drug', 'drug')}"
            )

        elif tier_score == 0:
            verdict = "UNSUPPORTED"
            confidence = 0.0
            rationale = "No evidence tier provided — claim is unsubstantiated"

        elif tier_raw == "T1" and p_value is not None and float(p_value) < 0.05:
            verdict = "PASS"
            confidence = cap_confidence(_T1_CAP)
            rationale = (
                f"T1 RCT evidence: p={p_value}, effect_size={effect_size} — "
                f"statistically significant"
            )

        elif tier_raw == "T1":
            verdict = "UNCERTAIN"
            confidence = cap_confidence(min(_BIOMED_CAP, 0.75))
            rationale = "T1 evidence tier declared but p-value absent or not significant"

        elif tier_score >= 2:
            raw_conf = _BIOMED_CAP * (tier_score / 4.0)
            verdict = "UNCERTAIN"
            confidence = cap_confidence(min(raw_conf, _BIOMED_CAP))
            rationale = (
                f"Evidence tier {tier_raw} — observational or lower; "
                f"clinical significance uncertain"
            )

        else:
            verdict = "UNCERTAIN"
            confidence = cap_confidence(0.30)
            rationale = (
                f"Weak evidence tier ({tier_raw}) — pre-clinical only; "
                f"insufficient for clinical claim"
            )

        receipt_id, lineage_hash = emit_lineage_receipt(
            claim_id=claim_id, domain=self.domain, adapter="fda_biomed",
            verdict=verdict, confidence=confidence, checks=checks,
        )
        return ValidationResult(
            claim_id=claim_id, domain=self.domain, adapter="fda_biomed",
            verdict=verdict, confidence=confidence, rationale=rationale,
            checks=checks, receipt_id=receipt_id, lineage_hash=lineage_hash,
        )
