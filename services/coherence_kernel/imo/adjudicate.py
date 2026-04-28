"""11-step adjudication pipeline for collapse-gate decisions."""
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from typing import Literal
from pathlib import Path
from services.coherence_kernel import schemas
from services.coherence_kernel.decoherence import aggregator
from services.coherence_kernel import readiness as readiness_mod
from services.coherence_kernel.imo import invariants as inv_mod
from services.coherence_kernel.storage import ledger

# Step labels (11 steps, deterministic order)
STEPS = [
    "LOAD_BRANCH",
    "COMPUTE_DECOHERENCE",
    "COMPUTE_READINESS",
    "CHECK_H1_MIN_READINESS",
    "CHECK_H2_PROVENANCE_DEPTH",
    "CHECK_H3_EVIDENCE_MAGNITUDE",
    "CHECK_H4_UNCERTAINTY_BOUNDED",
    "CHECK_H5_NO_DECOHERENCE_BREACH",
    "CHECK_H6_RECEIPT_CHAIN_VALID",
    "CHECK_H7_REVERSIBILITY_DOCUMENTED",
    "EVALUATE_ADVISORIES_EMIT_DECISION",
]


def _gate_decision(
    failures: list[str],
    dd: schemas.DecoherenceDetector,
) -> Literal["collapse_ready", "hold_ncom", "force_more_branches", "abort"]:
    n = len(failures)
    if n == 0:
        return "collapse_ready"
    if n == 1 and "H5_NO_DECOHERENCE_BREACH" in failures:
        return "hold_ncom"
    if n == 1:
        return "force_more_branches"
    return "abort"


def _imo_receipt(branch_id: str, step_trace: list[str], decision: str) -> str:
    raw = json.dumps({"branch_id": branch_id, "steps": step_trace, "decision": decision}, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def run(
    branch: schemas.BranchState,
    db_path: Path | None = None,
) -> schemas.PointerStatePromotion:
    """Execute the 11-step adjudication pipeline; returns PointerStatePromotion."""
    step_trace: list[str] = []

    # Step 1: LOAD_BRANCH
    step_trace.append(f"{STEPS[0]}:ok")

    # Step 2: COMPUTE_DECOHERENCE
    dd = aggregator.detect(branch)
    step_trace.append(f"{STEPS[1]}:aggregate={dd.aggregate:.4f}")

    # Step 3: COMPUTE_READINESS
    rs = readiness_mod.compute_readiness(branch, db_path=db_path)
    step_trace.append(f"{STEPS[2]}:score_100={rs.score_100:.4f}")

    # Steps 4–10: check H1–H7
    passed: list[str] = []
    failed: list[str] = []

    for i, inv in enumerate(inv_mod.HARD):
        step_label = STEPS[3 + i]
        result = inv.check(branch, rs, dd)
        if result:
            passed.append(inv.name)
            step_trace.append(f"{step_label}:PASS")
        else:
            failed.append(inv.name)
            step_trace.append(f"{step_label}:FAIL")

    # Step 11: advisories + decision
    advisories_passed: list[str] = []
    for adv in inv_mod.ADVISORY:
        if adv.check(branch, rs, dd):
            advisories_passed.append(adv.name)

    decision = _gate_decision(failed, dd)
    step_trace.append(f"{STEPS[10]}:decision={decision}")

    receipt = _imo_receipt(branch.id, step_trace, decision)
    reversibility_horizon = int(max(0.0, 3600.0 - branch.reversibility_cost * 36.0))

    promotion = schemas.PointerStatePromotion(
        branch_id=branch.id,
        gate_decision=decision,
        invariants_passed=passed,
        invariants_advisory=advisories_passed,
        imo_receipt=receipt,
        root_ledger_entry=None,
        reversibility_horizon_seconds=reversibility_horizon,
    )

    kwargs = {"db_path": db_path} if db_path else {}
    ledger.append_promotion(
        promotion.model_dump(mode="json"),
        branch.id,
        decision,
        **kwargs,
    )
    ledger.append_receipt(
        {"step_trace": step_trace, "promotion": promotion.model_dump(mode="json")},
        "imo.adjudicate",
        branch.id,
        **kwargs,
    )

    return promotion
