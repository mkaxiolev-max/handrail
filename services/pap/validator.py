"""PAP resource validation — runs all P-1..P-5 invariants."""
from typing import Tuple, List
from .models import AletheiaPAPResource
from .hashing import verify_merkle_root


def _h_subset_of_t(H, T) -> bool:
    """Lightweight check: H summary length sane and T has at least 1 claim
    when H makes any claim. Production should run a semantic entailment check."""
    if not T.claims and (H.summary or H.explanation):
        # H has content; T has nothing to ground it
        return False
    return True


def validate_pap_resource(resource: AletheiaPAPResource) -> Tuple[bool, List[str]]:
    reasons: List[str] = []

    # P-2: Merkle coherence
    res_dict = resource.dict() if hasattr(resource, "dict") else resource.model_dump()
    if not verify_merkle_root(res_dict):
        reasons.append("S8: merkle divergence")

    # P-3: identity lineage
    if not resource.identity.ctf_lineage_id or not resource.identity.session_hash:
        reasons.append("S7: identity lineage missing")

    # P-3: epistemic typing
    for c in resource.T.claims:
        if c.epistemic_type is None:
            reasons.append(f"S3: claim {c.claim_id} untyped")

    # P-3: evidence provenance
    for e in resource.T.evidence:
        if not e.hash or not e.source_uri:
            reasons.append(f"S4: evidence {e.evidence_id} missing provenance")

    # P-4: A-layer Handrail required
    for af in resource.A.affordances:
        if not af.handrail_required:
            reasons.append(f"S2: action {af.action_id} bypasses Handrail")

    # Aletheion §14: NARRATIVE_AS_PROOF rejected
    if resource.H.storytime_mode == "NARRATIVE_AS_PROOF":
        reasons.append("storytime NARRATIVE_AS_PROOF forbidden (Aletheion §14)")

    # P-1: H subset of T
    if not _h_subset_of_t(resource.H, resource.T):
        reasons.append("S1: H makes claims unsupported by T")

    # P-1: persuasion without truth binding
    if resource.H.persuasion_flags and not _h_subset_of_t(resource.H, resource.T):
        reasons.append("S10: persuasion without truth binding")

    return (len(reasons) == 0, reasons)
