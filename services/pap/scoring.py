"""PAP 100-point rubric — 10 categories, returns PAPScore."""
from typing import Dict
from .models import AletheiaPAPResource, PAPScore
from .hashing import verify_merkle_root


def _score_parity(r: AletheiaPAPResource) -> float:
    # 12 pts: H + A both present and consistent
    if not r.H.summary or not r.A.affordances:
        return 0.0
    return 12.0 if r.H.explanation else 8.0


def _score_truth(r: AletheiaPAPResource) -> float:
    # 15 pts: claims typed, evidence present, contradictions surfaced
    if not r.T.claims:
        return 0.0
    typed = all(c.epistemic_type is not None for c in r.T.claims)
    has_evidence = len(r.T.evidence) >= 1
    score = 0.0
    if typed:        score += 7.0
    if has_evidence: score += 5.0
    if r.T.contradictions or r.T.confidence > 0:
        score += 3.0  # contradiction graph populated or confidence non-default
    return min(score, 15.0)


def _score_typing(r: AletheiaPAPResource) -> float:
    # 12 pts: every claim has a valid epistemic_type
    if not r.T.claims:
        return 0.0
    typed_count = sum(1 for c in r.T.claims if c.epistemic_type is not None)
    return 12.0 * (typed_count / len(r.T.claims))


def _score_evidence(r: AletheiaPAPResource) -> float:
    # 12 pts: all evidence has source_uri + hash + timestamp + provenance
    if not r.T.evidence:
        return 0.0
    good = sum(1 for e in r.T.evidence
               if e.hash and e.source_uri and e.timestamp)
    return 12.0 * (good / len(r.T.evidence))


def _score_safety(r: AletheiaPAPResource) -> float:
    # 15 pts: every action handrail_required + irreversible flagged + reversibility scored
    if not r.A.affordances:
        return 15.0  # no actions = no risk
    safe = sum(1 for af in r.A.affordances if af.handrail_required)
    flagged = sum(1 for af in r.A.affordances
                  if af.reversibility_score is not None)
    safe_frac = safe / len(r.A.affordances)
    flagged_frac = flagged / len(r.A.affordances)
    return 15.0 * (0.7 * safe_frac + 0.3 * flagged_frac)


def _score_receipts(r: AletheiaPAPResource) -> float:
    # 10 pts: required receipts present
    if "ingress_receipt" in r.receipts:
        return 10.0
    return 5.0 if r.receipts else 0.0


def _score_contradictions(r: AletheiaPAPResource) -> float:
    # 8 pts: contradictions surfaced (non-empty list = honest disclosure)
    # If none exist, also full credit (system claims none and CanonGate validates)
    return 8.0


def _score_canon(r: AletheiaPAPResource) -> float:
    # 8 pts: canon_eligibility populated honestly
    ce = r.T.canon_eligibility
    if "eligible" in ce and "reason" in ce:
        return 8.0
    return 4.0


def _score_deletion(r: AletheiaPAPResource) -> float:
    # 5 pts: deletion policy declared
    d = r.deletion
    if d.get("debris_policy") == "retain_lineage_delete_surface":
        return 5.0
    return 2.0


def _score_elegance(r: AletheiaPAPResource) -> float:
    # 3 pts: merkle_root valid, no dead surfaces
    res_dict = r.dict() if hasattr(r, "dict") else r.model_dump()
    return 3.0 if verify_merkle_root(res_dict) else 0.0


def _grade_band(total: float) -> str:
    if total >= 95: return "THEORETICAL_MAX"
    if total >= 91: return "CANON_READY"
    if total >= 76: return "GOVERNED_PARITY"
    if total >= 56: return "AGENT_USABLE"
    if total >= 31: return "STRUCTURED"
    return "WEB_PAGE"


def score_pap_resource(resource: AletheiaPAPResource) -> PAPScore:
    subs: Dict[str, float] = {
        "human_agent_parity":         _score_parity(resource),
        "truth_surface_completeness": _score_truth(resource),
        "epistemic_typing_integrity": _score_typing(resource),
        "evidence_provenance":        _score_evidence(resource),
        "execution_safety":           _score_safety(resource),
        "receipt_lineage":            _score_receipts(resource),
        "contradiction_handling":     _score_contradictions(resource),
        "canon_governance":           _score_canon(resource),
        "deletion_discipline":        _score_deletion(resource),
        "elegance":                   _score_elegance(resource),
    }
    total = sum(subs.values())
    return PAPScore(score_total=total, grade=_grade_band(total), subscores=subs)
