from fastapi import APIRouter, HTTPException

from app.repositories.omega_runs import OmegaRunsRepository
from app.policy.guards import omega_pdp_guard, OmegaPolicyError

router = APIRouter(prefix="/omega", tags=["omega"])


def get_repository() -> OmegaRunsRepository:
    return OmegaRunsRepository()


@router.get("/runs")
async def list_runs():
    runs = get_repository().list_runs()
    return {"runs": runs, "total": len(runs)}


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    run = get_repository().get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Omega run {run_id} not found")
    return run


@router.get("/runs/{run_id}/branches")
async def list_branches(run_id: str):
    repository = get_repository()
    run = repository.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Omega run {run_id} not found")
    branches = repository.get_branches(run_id)
    return {"run_id": run_id, "branches": branches, "total": len(branches)}


@router.post("/runs/{run_id}/compare")
async def compare_run(run_id: str, payload: dict):
    # ── PDP guard on compare-to-reality ──────────────────────────────────────
    _operator = str((payload.get("observed_outcome") or {}).get("operator", "founder"))
    try:
        omega_pdp_guard(operator=_operator, run_id=run_id, can_alter_status=True)
    except OmegaPolicyError as _pe:
        raise HTTPException(status_code=403, detail={
            "error": "omega_pdp_denied",
            "verdict": _pe.verdict,
            "reason": _pe.reason,
            "policy_state": "denied",
        })
    # ─────────────────────────────────────────────────────────────────────────
    repository = get_repository()
    comparison = repository.compare_run_to_observed(run_id, payload)
    if not comparison:
        raise HTTPException(status_code=404, detail=f"Omega run {run_id} not found")
    return comparison
