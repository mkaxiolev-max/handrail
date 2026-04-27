"""Shared fixtures for PAP tests."""
import pytest
from datetime import datetime, timezone
from services.pap.models import (
    AletheiaPAPResource, HumanSurface, AgentSurface, TruthSurface,
    PAPAction, PAPClaim, PAPEvidence, PAPIdentity, EpistemicType,
)
from services.pap.hashing import compute_merkle_root


def _make_resource(
    *,
    claims=None, evidence=None, actions=None,
    storytime_mode="CANONICAL_EXPLANATION",
    handrail_required=True, persuasion_flags=None,
    skip_identity=False,
):
    H = HumanSurface(
        summary="A clearly evidenced summary.",
        explanation="An explanation derived from T-layer claims.",
        persuasion_flags=persuasion_flags or [],
        storytime_mode=storytime_mode,
    )
    if claims is None:
        claims = [PAPClaim(
            claim_id="c1", text="Sky is blue at noon over Mead WA.",
            epistemic_type=EpistemicType.OBSERVED_FACT,
            evidence_refs=["e1"], confidence=0.95,
        )]
    if evidence is None:
        evidence = [PAPEvidence(
            evidence_id="e1", source_uri="https://example.org/photo",
            hash="a" * 64, timestamp=datetime.now(timezone.utc),
            provenance={"author": "test"},
        )]
    if actions is None:
        actions = [PAPAction(
            action_id="get_status", endpoint="/handrail/ops/get",
            method="GET", reversibility_score=1.0, irreversible=False,
            handrail_required=handrail_required, required_receipts=["aletheion"],
        )]
    T = TruthSurface(
        claims=claims, evidence=evidence, contradictions=[],
        confidence=0.9,
        canon_eligibility={"eligible": False, "reason": "pending"},
    )
    A = AgentSurface(schema_ref="pap://schemas/test", affordances=actions)
    identity = PAPIdentity(
        actor_id="actor-1",
        session_hash="" if skip_identity else "s" * 64,
        ctf_lineage_id="" if skip_identity else "ctf://test",
    )
    merkle = compute_merkle_root(H, A, T)
    return AletheiaPAPResource(
        resource_id="uri://test/r1",
        merkle_root=merkle,
        identity=identity, H=H, A=A, T=T,
    )


@pytest.fixture
def clean_resource():
    return _make_resource()


@pytest.fixture
def make_resource():
    return _make_resource
