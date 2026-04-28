"""Branch registry — register and retrieve BranchState objects."""
from __future__ import annotations
import json
from services.coherence_kernel import schemas
from services.coherence_kernel.storage import ledger

_registry: dict[str, schemas.BranchState] = {}


def branch_register(branch: schemas.BranchState) -> str:
    rh = ledger.append_branch_state(branch.model_dump(mode="json"), branch.id)
    _registry[branch.id] = branch
    return rh


def get_branch(branch_id: str) -> schemas.BranchState | None:
    return _registry.get(branch_id)


def list_branches() -> list[str]:
    return list(_registry.keys())
