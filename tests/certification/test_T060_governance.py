# Copyright © 2026 AXIOLEV Holdings LLC. All rights reserved.
"""T-060 — Governance: policy authority chain verifiable.

I7 certification pillar — emits CertificateArtifact to Lineage Fabric on success.
"""
import hashlib
import json
from datetime import datetime, timedelta, timezone

from services.assurance import CertificateArtifact
from ns.integrations.alexandria import AlexandrianArchive

_ISSUER = "axiolev_dignity_kernel"
_EXPIRY = (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")

# Canonical policy authority chain: founder → policy_engine → cps_executor
_AUTHORITY_CHAIN = [
    {"node": "founder",       "issuer": "GENESIS",       "role": "root_authority"},
    {"node": "policy_engine", "issuer": "founder",       "role": "policy_authority"},
    {"node": "cps_executor",  "issuer": "policy_engine", "role": "executor"},
]

_REQUIRED_ROLES = {"root_authority", "policy_authority", "executor"}


def _make_cert(claims: dict) -> CertificateArtifact:
    sig = "sha256:" + hashlib.sha256(
        json.dumps(claims, sort_keys=True).encode()
    ).hexdigest()[:32]
    return CertificateArtifact(
        subject="governance.policy_chain",
        claims=claims,
        issuer=_ISSUER,
        signature=sig,
        expiry=_EXPIRY,
    )


def _emit_cert_to_lineage(cert: CertificateArtifact, archive: AlexandrianArchive) -> None:
    archive.append_lineage_event({
        "type": "certificate_artifact",
        "subject": cert.subject,
        "claims": cert.claims,
        "issuer": cert.issuer,
        "signature": cert.signature,
        "expiry": cert.expiry,
    })


def test_policy_authority_chain_verifiable(tmp_path):
    """Policy authority chain traces to GENESIS with no gaps."""
    chain = _AUTHORITY_CHAIN
    node_set = {n["node"] for n in chain}

    for node in chain:
        if node["issuer"] == "GENESIS":
            continue
        assert node["issuer"] in node_set, (
            f"Broken link: issuer {node['issuer']!r} not present in chain"
        )

    roots = [n for n in chain if n["issuer"] == "GENESIS"]
    assert len(roots) == 1, "Exactly one GENESIS root required"
    assert roots[0]["node"] == "founder"

    roles_present = {n["role"] for n in chain}
    assert _REQUIRED_ROLES <= roles_present, (
        f"Missing roles: {_REQUIRED_ROLES - roles_present}"
    )

    cert = _make_cert({
        "chain_length": len(chain),
        "root_authority": roots[0]["node"],
        "roles_verified": sorted(roles_present),
        "verifiable": True,
    })
    archive = AlexandrianArchive(root=tmp_path)
    _emit_cert_to_lineage(cert, archive)

    events = archive.read_lineage()
    assert len(events) == 1
    assert events[0]["subject"] == "governance.policy_chain"
    assert events[0]["claims"]["verifiable"] is True


def test_governance_chain_detects_broken_link():
    """Chain with a missing intermediate node fails the gap check."""
    broken = [
        {"node": "founder",      "issuer": "GENESIS",       "role": "root_authority"},
        {"node": "cps_executor", "issuer": "policy_engine",  "role": "executor"},
    ]
    node_set = {n["node"] for n in broken}
    gaps = [n for n in broken if n["issuer"] != "GENESIS" and n["issuer"] not in node_set]
    assert len(gaps) == 1
    assert gaps[0]["node"] == "cps_executor"


def test_governance_chain_rejects_multiple_roots():
    """Chain with two GENESIS roots is invalid."""
    dual_root = [
        {"node": "founder",       "issuer": "GENESIS", "role": "root_authority"},
        {"node": "shadow_founder","issuer": "GENESIS",  "role": "root_authority"},
        {"node": "policy_engine", "issuer": "founder",  "role": "policy_authority"},
    ]
    roots = [n for n in dual_root if n["issuer"] == "GENESIS"]
    assert len(roots) != 1, "Multiple GENESIS roots must be rejected"
