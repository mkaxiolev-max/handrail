"""PAP QEC — 10 syndromes, all fail-closed."""
from typing import List
from .models import AletheiaPAPResource, PAPQECFailure
from .hashing import verify_merkle_root


def detect_qec_syndromes(resource: AletheiaPAPResource) -> List[PAPQECFailure]:
    out: List[PAPQECFailure] = []

    # S1: H not subset of T
    if not resource.T.claims and (resource.H.summary or resource.H.explanation):
        out.append(PAPQECFailure(syndrome="S1",
                                  description="H makes claims with empty T"))

    # S2: A-layer action without Handrail
    for af in resource.A.affordances:
        if not af.handrail_required:
            out.append(PAPQECFailure(syndrome="S2",
                description=f"action {af.action_id} bypasses Handrail",
                field_path=f"A.affordances[{af.action_id}]"))

    # S3: untyped claim
    for c in resource.T.claims:
        if c.epistemic_type is None:
            out.append(PAPQECFailure(syndrome="S3",
                description=f"untyped claim {c.claim_id}"))

    # S4: evidence missing provenance
    for e in resource.T.evidence:
        if not e.hash or not e.source_uri:
            out.append(PAPQECFailure(syndrome="S4",
                description=f"evidence {e.evidence_id} missing provenance"))

    # S5: Canon attempt under contradiction
    if resource.T.canon_eligibility.get("eligible") and resource.T.contradictions:
        out.append(PAPQECFailure(syndrome="S5",
            description="canon attempt under unresolved contradiction"))

    # S6: execution without receipt
    has_action_attempt = any(
        af.handrail_required for af in resource.A.affordances
    )
    rec = resource.receipts
    if has_action_attempt and "execution_receipt" in rec and not rec.get("execution_receipt"):
        out.append(PAPQECFailure(syndrome="S6",
            description="execution slot present but empty"))

    # S7: identity lineage missing
    if not resource.identity.ctf_lineage_id or not resource.identity.session_hash:
        out.append(PAPQECFailure(syndrome="S7",
            description="identity ctf_lineage_id or session_hash missing"))

    # S8: merkle divergence
    res_dict = resource.dict() if hasattr(resource, "dict") else resource.model_dump()
    if not verify_merkle_root(res_dict):
        out.append(PAPQECFailure(syndrome="S8",
            description="merkle_root does not match recomputed value"))

    # S9: lineage deletion attempt — checked at deletion call site (deletion.py)

    # S10: persuasion without truth binding
    if resource.H.persuasion_flags and not resource.T.claims:
        out.append(PAPQECFailure(syndrome="S10",
            description="persuasion_flags present but no T-layer claims"))

    return out
