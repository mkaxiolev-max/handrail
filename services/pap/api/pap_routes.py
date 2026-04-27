"""PAP HTTP endpoints."""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime, timezone

from ..models import (
    AletheiaPAPResource, PAPClaim, PAPAction,
    PAPScore, PAPQECFailure, TriadicScore,
)
from ..validator import validate_pap_resource
from ..scoring import score_pap_resource
from ..qec import detect_qec_syndromes
from ..canon_bridge import triadic_canon_check, can_promote_to_canon_via_pap
from ..aletheion_bridge import wrap_aletheion_gates
from ..receipts import write_pap_receipt, read_pap_receipt
from ..storytime_bridge import render_h_layer

router = APIRouter(prefix="/pap", tags=["pap"])


@router.get("/healthz")
def healthz() -> Dict[str, Any]:
    return {
        "ok": True,
        "service": "pap",
        "version": "1.0",
        "wraps": "aletheion v2.0",
        "ts": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/parse")
def parse_resource(body: Dict[str, Any]) -> Dict[str, Any]:
    try:
        r = AletheiaPAPResource(**body)
        return {"ok": True, "resource_id": r.resource_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/validate")
def validate(body: Dict[str, Any]) -> Dict[str, Any]:
    r = AletheiaPAPResource(**body)
    ok, reasons = validate_pap_resource(r)
    return {"ok": ok, "reasons": reasons}


@router.post("/score")
def score(body: Dict[str, Any]) -> Dict[str, Any]:
    r = AletheiaPAPResource(**body)
    s: PAPScore = score_pap_resource(r)
    return s.dict() if hasattr(s, "dict") else s.model_dump()


@router.post("/qec")
def qec(body: Dict[str, Any]) -> Dict[str, Any]:
    r = AletheiaPAPResource(**body)
    syndromes = detect_qec_syndromes(r)
    return {"count": len(syndromes),
            "syndromes": [s.dict() if hasattr(s, "dict") else s.model_dump()
                          for s in syndromes]}


@router.post("/action/check")
def action_check(body: Dict[str, Any]) -> Dict[str, Any]:
    """Run Aletheion three-gate wrap on a proposed action."""
    action = PAPAction(**body["action"])
    claim = PAPClaim(**body["claim"])
    return wrap_aletheion_gates(
        action, claim,
        body.get("logos_check", {"subject_id": claim.claim_id,
                                 "truth_coherence": 1.0, "dignity_preservation": 1.0,
                                 "humility_alignment": 1.0, "love_vector": 1.0,
                                 "coercion_risk": 0.0, "domination_risk": 0.0,
                                 "deception_risk": 0.0,
                                 "sacred_language_override_risk": 0.0}),
        body.get("signal", {}),
        body.get("ctx", {}),
    )


@router.post("/canon/check")
def canon_check(body: Dict[str, Any]) -> Dict[str, Any]:
    """Triadic Canon check. Decree P-6."""
    ldr = float(body["ldr_score"])
    omega = float(body["omega_gnoseo_score"])
    pap = float(body["pap_score"])
    eligible, tmin, blocker = triadic_canon_check(ldr, omega, pap)
    ts = TriadicScore(
        ldr_score=ldr, omega_gnoseo_score=omega, pap_score=pap,
        triadic_min=tmin, canon_eligible=eligible, blocking_track=blocker,
    )
    return ts.dict() if hasattr(ts, "dict") else ts.model_dump()


@router.get("/receipt/{rid}")
def receipt(rid: str) -> Dict[str, Any]:
    r = read_pap_receipt(rid)
    if r is None:
        raise HTTPException(status_code=404, detail="receipt not found")
    return r.dict() if hasattr(r, "dict") else r.model_dump()


@router.get("/dashboard")
def dashboard() -> Dict[str, Any]:
    import json
    from pathlib import Path
    p = Path(".run/pap/dashboard.json")
    if p.exists():
        return json.loads(p.read_text())
    return {"system": "NS∞", "layer": "PAP", "version": "1.0", "wraps": "aletheion v2.0"}
