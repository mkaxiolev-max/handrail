"""PAP -> Aletheion bridge. PAP wraps; Aletheion gates."""
from typing import Dict, Any, Optional
from .models import PAPAction, PAPClaim


def call_logos_gate(logos_check: Dict[str, Any]) -> Dict[str, Any]:
    """POST /aletheion/logos-gate. Returns {decision, reasons, receipt_id}."""
    try:
        from services.aletheion.logos_gate import logos_gate, LogosConstraintCheck
        check = LogosConstraintCheck(**logos_check)
        result = logos_gate(check)
        return {
            "decision": result.decision,
            "reasons": result.reasons,
            "receipt_id": logos_check.get("subject_id", "no-receipt"),
        }
    except ImportError:
        return {"decision": "DENY", "reasons": ["aletheion not importable"], "receipt_id": None}


def call_canon_gate(claim: PAPClaim, ctx: Dict[str, Any]) -> Dict[str, Any]:
    """POST /aletheion/canon-gate."""
    try:
        from services.aletheion.canon_readiness import (
            assess_canon_readiness, CanonReadinessRequest,
        )
        req = CanonReadinessRequest(
            claim_id=claim.claim_id,
            evidence_refs=claim.evidence_refs,
            contradiction_score=ctx.get("contradiction_score", 0.0),
            admissibility_score=ctx.get("admissibility_score", claim.confidence),
            constraint_score=ctx.get("constraint_score", 1.0),
            logos_score=ctx.get("logos_score", 1.0),
            narrative_contamination_risk=ctx.get("narrative_contamination_risk", 0.0),
        )
        resp = assess_canon_readiness(req)
        return {
            "decision": resp.decision,
            "score": resp.canon_readiness_score,
            "reasons": resp.reasons,
            "receipt_id": claim.claim_id,
        }
    except ImportError:
        return {"decision": "DENY", "score": 0.0, "reasons": ["aletheion not importable"], "receipt_id": None}


def call_pre_action_gate(action: PAPAction, signal: Dict[str, Any], logos: Dict[str, Any]) -> Dict[str, Any]:
    """POST /aletheion/pre-action-check."""
    try:
        from services.aletheion.pre_action import pre_action_check
        # Build minimal duck-typed objects
        class _S:
            def __init__(self, d): self.__dict__.update(d)
        sig = _S({**{
            "dignity_sensitivity": 0.0,
            "narrative_collapse_risk": 0.0,
        }, **signal})
        log = _S({**{
            "deception_risk": 0.0, "coercion_risk": 0.0, "domination_risk": 0.0,
            "truth_coherence": 1.0, "dignity_preservation": 1.0,
        }, **logos})
        decision = pre_action_check(action, sig, log)
        return {"decision": decision, "receipt_id": action.action_id}
    except ImportError:
        return {"decision": "DENY", "receipt_id": None}


def wrap_aletheion_gates(action: PAPAction, claim: PAPClaim,
                         logos_check: Dict[str, Any],
                         signal: Dict[str, Any],
                         ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Decree P-4: PAP routes A-layer through all three Aletheion gates."""
    logos = call_logos_gate(logos_check)
    if logos["decision"] == "HARD_STOP":
        return {"logos": logos, "canon": None, "pre_action": None,
                "admit": False, "reasons": logos["reasons"]}
    canon = call_canon_gate(claim, ctx)
    if canon["decision"] not in ("ALLOW",):
        return {"logos": logos, "canon": canon, "pre_action": None,
                "admit": False, "reasons": canon["reasons"]}
    pre = call_pre_action_gate(action, signal, logos)
    admit = (logos["decision"] == "ALLOW"
             and canon["decision"] == "ALLOW"
             and pre["decision"] == "ADMIT")
    reasons = []
    if logos["decision"] != "ALLOW": reasons.append(f"logos: {logos['decision']}")
    if canon["decision"] != "ALLOW": reasons.append(f"canon: {canon['decision']}")
    if pre["decision"] != "ADMIT":   reasons.append(f"pre_action: {pre['decision']}")
    return {"logos": logos, "canon": canon, "pre_action": pre,
            "admit": admit, "reasons": reasons}
