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
  claim_id        — str (auto-generated if absent)
  actor           — str: submitter identifier for audit trail (default: "system")
  evidence_tier   — "T1" | "T2" | "T3" | "T4"
  drug            — str: drug name for dosage-limit lookup
  population      — str: patient population description
  indication      — str: clinical indication
  contraindicated — bool: caller-attested contraindication flag
  p_value         — float: reported p-value (T1 claims)
  effect_size     — float | str: reported effect size

Lineage Fabric: every result anchored to a chained receipt.
"""
from __future__ import annotations

import re
import time
import uuid
from typing import Any, Dict, List

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
        result["within_known_limit"]  = dosage_val <= limit
        result["known_limit_mg_day"]  = limit
    return result


def _ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class FDABiomedAdapter:
    domain = "biomedical"

    def validate(self, claim: str, context: Dict[str, Any]) -> ValidationResult:
        claim_id = context.get("claim_id", uuid.uuid4().hex[:12])
        actor    = context.get("actor", "system")
        flags: List[str] = []
        audit: List[Dict[str, Any]] = []

        # ── Audit entry 1: intake ──────────────────────────────────────────────
        audit.append({
            "step": "intake",
            "ts": _ts(),
            "actor": actor,
            "claim_id": claim_id,
            "regulatory_framework": "FDA 21 CFR Part 11 / ICH E6(R2)",
            "claim_len": len(claim),
        })

        checks: Dict[str, Any] = {
            "regulatory_framework": "FDA 21 CFR Part 11 / ICH E6(R2)",
            "audit_trail": True,
        }

        # ── Evidence tier ──────────────────────────────────────────────────────
        tier_raw  = str(context.get("evidence_tier", "")).upper()
        tier_score = _EVIDENCE_TIERS.get(tier_raw, 0)
        checks["evidence_tier"] = tier_raw or "UNSUPPORTED"
        checks["tier_score"]    = tier_score
        tier_ok = tier_score > 0
        if not tier_ok:
            flags.append("evidence_tier_missing_or_invalid")
        audit.append({"step": "evidence_tier", "ts": _ts(), "tier": tier_raw,
                      "tier_score": tier_score, "ok": tier_ok, "actor": actor})

        # ── Dosage check ───────────────────────────────────────────────────────
        dosage_check = _check_dosage(claim, context)
        checks["dosage"] = dosage_check
        dosage_flag_ok = dosage_check.get("within_known_limit", True)  # True if no limit known
        if dosage_check.get("within_known_limit") is False:
            flags.append("dosage_exceeds_known_limit")
        audit.append({"step": "dosage_check", "ts": _ts(), "result": dosage_check,
                      "ok": dosage_flag_ok, "actor": actor})

        # ── Population / indication ────────────────────────────────────────────
        population = context.get("population", "")
        indication = context.get("indication", "")
        checks["population"] = population
        checks["indication"]  = indication
        if not population:
            flags.append("population_not_specified")
        if not indication:
            flags.append("indication_not_specified")
        audit.append({"step": "population_indication", "ts": _ts(),
                      "population": population, "indication": indication,
                      "ok": bool(population and indication), "actor": actor})

        # ── Contraindication flag ──────────────────────────────────────────────
        contraindicated = context.get("contraindicated", False)
        checks["contraindicated"] = contraindicated
        if contraindicated:
            flags.append("contraindication_declared")
        audit.append({"step": "contraindication", "ts": _ts(),
                      "contraindicated": contraindicated, "actor": actor})

        # ── Statistical evidence (T1) ──────────────────────────────────────────
        p_value     = context.get("p_value")
        effect_size = context.get("effect_size")
        checks["p_value"]     = p_value
        checks["effect_size"] = effect_size
        sig_ok = (p_value is not None and float(p_value) < 0.05) if p_value is not None else False
        if tier_raw == "T1" and not sig_ok:
            flags.append("t1_without_significant_p_value")
        audit.append({"step": "statistical_evidence", "ts": _ts(),
                      "p_value": p_value, "effect_size": effect_size,
                      "significant": sig_ok, "actor": actor})

        # ── Verdict ────────────────────────────────────────────────────────────
        if contraindicated:
            verdict: Verdict = "FAIL"
            confidence = cap_confidence(0.92)
            rationale  = "Contraindication flag set — claim is clinically unsafe"

        elif dosage_check.get("within_known_limit") is False:
            verdict    = "FAIL"
            confidence = cap_confidence(0.88)
            rationale  = (
                f"Dosage {dosage_check['value']} {dosage_check['unit']} exceeds "
                f"known safe limit {dosage_check.get('known_limit_mg_day')} mg/day "
                f"for {dosage_check.get('drug', 'drug')}"
            )

        elif tier_score == 0:
            verdict    = "UNSUPPORTED"
            confidence = 0.0
            rationale  = "No evidence tier provided — claim is unsubstantiated"

        elif tier_raw == "T1" and sig_ok:
            verdict    = "PASS"
            confidence = cap_confidence(_T1_CAP)
            rationale  = (
                f"T1 RCT evidence: p={p_value}, effect_size={effect_size} — "
                f"statistically significant"
            )

        elif tier_raw == "T1":
            verdict    = "UNCERTAIN"
            confidence = cap_confidence(min(_BIOMED_CAP, 0.75))
            rationale  = "T1 evidence tier declared but p-value absent or not significant"

        elif tier_score >= 2:
            raw_conf   = _BIOMED_CAP * (tier_score / 4.0)
            verdict    = "UNCERTAIN"
            confidence = cap_confidence(min(raw_conf, _BIOMED_CAP))
            rationale  = (
                f"Evidence tier {tier_raw} — observational or lower; "
                f"clinical significance uncertain"
            )

        else:
            verdict    = "UNCERTAIN"
            confidence = cap_confidence(0.30)
            rationale  = (
                f"Weak evidence tier ({tier_raw}) — pre-clinical only; "
                f"insufficient for clinical claim"
            )

        # ── Audit entry: decision + electronic signature placeholder ───────────
        audit.append({
            "step": "decision",
            "ts": _ts(),
            "verdict": verdict,
            "confidence": confidence,
            "flags": list(flags),
            "actor": actor,
            "electronic_signature_placeholder": f"esig://{actor}/{claim_id[:8]}",
        })

        receipt_id, lineage_hash = emit_lineage_receipt(
            claim_id=claim_id, domain=self.domain, adapter="fda_biomed",
            verdict=verdict, confidence=confidence, checks=checks,
        )
        return ValidationResult(
            claim_id=claim_id, domain=self.domain, adapter="fda_biomed",
            verdict=verdict, confidence=confidence, rationale=rationale,
            checks=checks, flags=flags, audit_trail=audit,
            receipt_id=receipt_id, lineage_hash=lineage_hash,
        )
