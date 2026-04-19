"""
axiolev-omega-api-v2
AXIOLEV Holdings LLC © 2026

FastAPI routes per Omega Whitepaper.
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List

from .primitives import (
    Branch, Delta, ProjectionRequest, ProjectionResult,
    Storytime, ConfidenceEnvelope, ProjectionMode, Recoverability,
)
from .canon_gate import canon_gate
from .ctf import emit_receipt
from .hic import compile_intent
from .pdp import evaluate as pdp_evaluate


router = APIRouter(tags=["omega"])


@router.get("/healthz")
def healthz() -> Dict[str, str]:
    return {"status": "ok", "layer": "L10"}


@router.post("/branches")
def create_branch(branch: Branch) -> Branch:
    emit_receipt("branch_created", branch.id, "ok", branch.title)
    return branch


@router.post("/deltas")
def create_delta(delta: Delta) -> Delta:
    emit_receipt("delta_created", delta.id, "ok", delta.branch_id)
    return delta


@router.post("/projections", response_model=ProjectionResult)
def create_projection(req: ProjectionRequest) -> ProjectionResult:
    conf = ConfidenceEnvelope(evidence=0.8, contradiction=0.1, novelty=0.3, stability=0.8)
    result = ProjectionResult(
        request_id=req.id,
        branch_id=req.branch_id,
        mode=req.mode,
        confidence=conf,
        recoverability=Recoverability.EXACT,
        order_used=[],
        payload={},
    )
    emit_receipt("projection_emitted", req.id, "ok", req.branch_id)
    return result


@router.post("/canon/promote")
def promote_to_canon(
    confidence: ConfidenceEnvelope,
    reconstructability: float,
    lineage_valid: bool,
    hic_receipt: str,
    pdp_receipt: str,
) -> Dict[str, Any]:
    decision = canon_gate(confidence, reconstructability, lineage_valid,
                          hic_receipt, pdp_receipt)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail={
            "event": "canon_gate_denied",
            "reasons": decision.reasons,
        })
    emit_receipt("canon_promoted_with_hardware_quorum",
                 hic_receipt, "ok", ",".join(decision.reasons) or "passed")
    return {"allowed": True, "reasons": decision.reasons}


@router.post("/hic/decisions")
def hic_decision(intent_id: str, rationale: str, serials: List[str]) -> Dict[str, Any]:
    d = compile_intent(intent_id, rationale, serials)
    emit_receipt("hic_decision", intent_id, "ok" if d.approved else "denied", rationale)
    return {"approved": d.approved, "rationale": d.rationale, "serials": d.yubikey_serials}


@router.post("/pdp/evaluate")
def pdp_evaluate_route(principal: str, action: str, resource: str) -> Dict[str, Any]:
    d = pdp_evaluate(principal, action, resource)
    emit_receipt("pdp_evaluated", f"{principal}:{action}:{resource}",
                 "ok" if d.allowed else "denied", d.reason)
    return {"allowed": d.allowed, "reason": d.reason}


@router.get("/ctf/receipts")
def list_ctf_receipts() -> Dict[str, Any]:
    return {"ledger": "/Volumes/NSExternal/ALEXANDRIA/ledger/ns_events.jsonl",
            "ctf_dir": "/Volumes/NSExternal/ALEXANDRIA/ctf/receipts"}


@router.post("/storytime")
def create_storytime(st: Storytime) -> Storytime:
    emit_receipt("storytime_emitted", st.id, "ok", st.branch_id)
    return st


@router.get("/storytime/{sid}")
def get_storytime(sid: str) -> Dict[str, Any]:
    return {"id": sid, "status": "not_found"}
