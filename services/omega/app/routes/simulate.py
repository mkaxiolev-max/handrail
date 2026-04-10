from fastapi import APIRouter, HTTPException

from app.engine.simulation_runner import run_simulation
from app.models.inputs import OmegaStateInput
from app.models.outputs import (
    OmegaBranch,
    OmegaConfidenceGeometry,
    OmegaFounderEnvelope,
    OmegaSummary,
)
from app.models.run_record import OmegaRunRecord
from app.repositories.omega_runs import OmegaReceiptBridge, OmegaRunsRepository
from app.policy.guards import (
    omega_hic_guard,
    OmegaPolicyError,
    build_policy_state,
    ADVISORY_ONLY,
)

router = APIRouter(prefix="/omega", tags=["omega"])


def get_repository() -> OmegaRunsRepository:
    return OmegaRunsRepository()


def get_receipt_bridge() -> OmegaReceiptBridge:
    return OmegaReceiptBridge()


@router.post("/simulate", response_model=OmegaFounderEnvelope)
async def simulate(payload: OmegaStateInput):
    # ── HIC policy guard ──────────────────────────────────────────────────────
    # Advisory-only by default. Promotion/execution paths require HIC clearance.
    _allow_promotion = payload.constraints.get("allow_promotion", False)
    _allow_execution = payload.constraints.get("allow_execution", False)
    _operator = str(payload.metadata.get("actor", "founder"))
    _intent_text = f"{payload.domain_type} {payload.bounded_context.get('description','')}"
    try:
        _policy_state = omega_hic_guard(
            intent=_intent_text,
            allow_promotion=bool(_allow_promotion),
            allow_execution=bool(_allow_execution),
            operator=_operator,
        )
    except OmegaPolicyError as _pe:
        raise HTTPException(status_code=403, detail={
            "error": "omega_policy_veto",
            "verdict": _pe.verdict,
            "reason": _pe.reason,
            "policy_state": "vetoed",
            "promotion_allowed": False,
        })
    # ─────────────────────────────────────────────────────────────────────────

    result = await run_simulation(payload)
    receipt_info = get_receipt_bridge().issue_run_receipt(
        run_id=result["run_id"],
        actor=str(payload.metadata.get("actor", "omega_service")),
        input_payload=payload.model_dump(mode="json"),
        result_payload={
            "summary": result["summary"],
            "divergence": result["divergence"],
            "confidence": result["confidence"],
        },
    )
    run_record = OmegaRunRecord(
        run_id=result["run_id"],
        actor=str(payload.metadata.get("actor", "omega_service")),
        domain_type=payload.domain_type,
        input_ref=payload.state_id,
        branch_count=payload.branch_count,
        horizon=payload.simulation_horizon,
        status="simulated",
        receipt_hash=receipt_info["receipt_hash"],
        chain_verified=receipt_info["chain_verified"],
        metadata={
            "receipt_id": receipt_info["receipt_id"],
            "source_refs": payload.source_refs,
            "receipt_refs": payload.receipt_refs,
            "seed": result["normalized_input"]["seed"],
        },
    )
    repository = get_repository()
    repository.create_run(
        run_record,
        input_payload=payload.model_dump(mode="json"),
        summary_payload=result["summary"],
        canon_version=payload.canon_version,
    )
    repository.create_branches(run_record.run_id, result["branches"])
    memory_refs = repository.write_summary_atom(run_record, result["summary"])
    run_record.memory_refs = memory_refs

    return OmegaFounderEnvelope(
        status="simulated",
        run_id=result["run_id"],
        receipt_hash=receipt_info["receipt_hash"],
        chain_verified=receipt_info["chain_verified"],
        divergence_score=result["divergence"]["divergence_score"],
        confidence=OmegaConfidenceGeometry(**result["confidence"]),
        warnings=result["warnings"],
        summary=OmegaSummary(**result["summary"]),
        branches=[OmegaBranch(**branch) for branch in result["branches"]],
        memory_atoms_written=len(memory_refs),
        canon_version=payload.canon_version,
        policy_state=_policy_state,
        promotion_allowed=False,
        execution_allowed=False,
    )
