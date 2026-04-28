"""IMO gate — 4 canonical verbs: propose, adjudicate, override, archive."""
from __future__ import annotations
import hashlib, json, uuid
from datetime import datetime, timezone
from pathlib import Path
from services.coherence_kernel import schemas
from services.coherence_kernel.imo import adjudicate as adj_mod
from services.coherence_kernel.imo import chamber
from services.coherence_kernel.storage import ledger

# In-memory proposal registry {proposal_id: BranchState}
_proposals: dict[str, schemas.BranchState] = {}
# Final decisions {proposal_id: PointerStatePromotion}
_decisions: dict[str, schemas.PointerStatePromotion] = {}


def propose(branch: schemas.BranchState) -> str:
    """Register branch for gate adjudication. Returns proposal_id."""
    proposal_id = str(uuid.uuid4())
    _proposals[proposal_id] = branch
    return proposal_id


def adjudicate(proposal_id: str, db_path: Path | None = None) -> schemas.PointerStatePromotion:
    """Run 11-step pipeline for the registered proposal. Returns PointerStatePromotion."""
    branch = _proposals.get(proposal_id)
    if branch is None:
        raise KeyError(f"no proposal registered for id={proposal_id!r}")
    promotion = adj_mod.run(branch, db_path=db_path)
    _decisions[proposal_id] = promotion
    return promotion


def override(
    proposal_id: str,
    reason: str,
    yubikey_receipt: str,
    db_path: Path | None = None,
) -> schemas.PointerStatePromotion:
    """Written override — bypasses hard invariant failures with chamber quorum.

    Requires non-empty reason and valid 64-char hex yubikey_receipt.
    Produces a collapse_ready decision regardless of invariant state.
    """
    chamber.validate_override(reason, yubikey_receipt)

    branch = _proposals.get(proposal_id)
    if branch is None:
        raise KeyError(f"no proposal registered for id={proposal_id!r}")

    override_receipt = hashlib.sha256(
        f"override:{proposal_id}:{yubikey_receipt}:{reason}".encode()
    ).hexdigest()

    promotion = schemas.PointerStatePromotion(
        branch_id=branch.id,
        gate_decision="collapse_ready",
        invariants_passed=["OVERRIDE"],
        invariants_advisory=[],
        imo_receipt=override_receipt,
        root_ledger_entry=f"OVERRIDE:{yubikey_receipt[:16]}",
        reversibility_horizon_seconds=0,
    )
    _decisions[proposal_id] = promotion

    kwargs = {"db_path": db_path} if db_path else {}
    ledger.append_promotion(promotion.model_dump(mode="json"), branch.id, "collapse_ready", **kwargs)
    ledger.append_receipt(
        {"override_reason": reason, "yubikey_receipt": yubikey_receipt, "promotion": promotion.model_dump(mode="json")},
        "imo.override",
        branch.id,
        **kwargs,
    )
    return promotion


def archive(proposal_id: str, db_path: Path | None = None) -> str:
    """Append final decision to ledger and clean up proposal registry. Returns row_hash."""
    decision = _decisions.get(proposal_id)
    if decision is None:
        raise KeyError(f"no decision found for proposal_id={proposal_id!r}; adjudicate first")

    kwargs = {"db_path": db_path} if db_path else {}
    row_hash = ledger.append_receipt(
        {"archived_proposal_id": proposal_id, "promotion": decision.model_dump(mode="json")},
        "imo.archive",
        decision.branch_id,
        **kwargs,
    )
    _proposals.pop(proposal_id, None)
    _decisions.pop(proposal_id, None)
    return row_hash
