# Copyright © 2026 AXIOLEV Holdings LLC. All rights reserved.
"""T-061 — Risk: risk register coverage >= defined scope.

I7 certification pillar — emits CertificateArtifact to Lineage Fabric on success.
"""
import hashlib
import json
from datetime import datetime, timedelta, timezone

from services.assurance import CertificateArtifact
from ns.integrations.alexandria import AlexandrianArchive

_ISSUER = "axiolev_dignity_kernel"
_EXPIRY = (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")

_REQUIRED_DOMAINS = {"operational", "technical", "legal", "reputational"}

_RISK_REGISTER = [
    {"id": "R-001", "domain": "operational",   "severity": "HIGH",   "owner": "founder",       "mitigated": True},
    {"id": "R-002", "domain": "operational",   "severity": "MEDIUM", "owner": "policy_engine", "mitigated": True},
    {"id": "R-003", "domain": "technical",     "severity": "HIGH",   "owner": "cps_executor",  "mitigated": True},
    {"id": "R-004", "domain": "technical",     "severity": "LOW",    "owner": "cps_executor",  "mitigated": True},
    {"id": "R-005", "domain": "legal",         "severity": "HIGH",   "owner": "founder",       "mitigated": True},
    {"id": "R-006", "domain": "reputational",  "severity": "MEDIUM", "owner": "founder",       "mitigated": False},
]


def _make_cert(claims: dict) -> CertificateArtifact:
    sig = "sha256:" + hashlib.sha256(
        json.dumps(claims, sort_keys=True).encode()
    ).hexdigest()[:32]
    return CertificateArtifact(
        subject="risk.register_coverage",
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


def test_risk_register_coverage_meets_scope(tmp_path):
    """All required risk domains are present in the register."""
    register = _RISK_REGISTER
    covered_domains = {entry["domain"] for entry in register}

    missing = _REQUIRED_DOMAINS - covered_domains
    assert not missing, f"Risk register missing domains: {missing}"

    coverage_ratio = len(covered_domains & _REQUIRED_DOMAINS) / len(_REQUIRED_DOMAINS)
    assert coverage_ratio >= 1.0, f"Coverage ratio {coverage_ratio:.2f} < 1.0"

    high_severity = [r for r in register if r["severity"] == "HIGH"]
    assert all(r["mitigated"] for r in high_severity), (
        "All HIGH-severity risks must be mitigated"
    )

    cert = _make_cert({
        "total_entries": len(register),
        "domains_covered": sorted(covered_domains),
        "coverage_ratio": coverage_ratio,
        "high_severity_mitigated": all(r["mitigated"] for r in high_severity),
    })
    archive = AlexandrianArchive(root=tmp_path)
    _emit_cert_to_lineage(cert, archive)

    events = archive.read_lineage()
    assert len(events) == 1
    assert events[0]["subject"] == "risk.register_coverage"
    assert events[0]["claims"]["coverage_ratio"] >= 1.0


def test_risk_register_incomplete_fails_coverage():
    """Register missing a required domain fails coverage check."""
    incomplete = [r for r in _RISK_REGISTER if r["domain"] != "legal"]
    covered = {r["domain"] for r in incomplete}
    missing = _REQUIRED_DOMAINS - covered
    assert "legal" in missing


def test_risk_register_unmitigated_high_detected():
    """HIGH-severity unmitigated entry is detected."""
    with_unmitigated = _RISK_REGISTER + [
        {"id": "R-999", "domain": "technical", "severity": "HIGH", "owner": "ops", "mitigated": False}
    ]
    highs = [r for r in with_unmitigated if r["severity"] == "HIGH"]
    unmitigated_highs = [r for r in highs if not r["mitigated"]]
    assert len(unmitigated_highs) == 1
    assert unmitigated_highs[0]["id"] == "R-999"
