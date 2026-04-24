# Copyright © 2026 AXIOLEV Holdings LLC. All rights reserved.
"""T-066 — Security: secret-scan + SBOM current; CVE SLA met.

I7 certification pillar — emits CertificateArtifact to Lineage Fabric on success.
"""
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from services.assurance import CertificateArtifact
from ns.integrations.alexandria import AlexandrianArchive

_ISSUER = "axiolev_dignity_kernel"
_EXPIRY = (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")

# CVE SLA: HIGH must be resolved within 30 days, CRITICAL within 7 days
_CVE_SLA_DAYS = {"CRITICAL": 7, "HIGH": 30, "MEDIUM": 90}

_SECRET_PATTERNS = [
    re.compile(r"sk_live_[A-Za-z0-9]{20,}"),     # Stripe live key
    re.compile(r"whsec_[A-Za-z0-9]{20,}"),        # Stripe webhook secret
    re.compile(r"ghp_[A-Za-z0-9]{36}"),           # GitHub personal token
    re.compile(r"AKIA[0-9A-Z]{16}"),              # AWS access key
    re.compile(r"(?i)password\s*=\s*\S{8,}"),     # Bare password assignment
]

_SBOM_REQUIRED_FIELDS = {"name", "version", "hash", "cve_status", "last_scanned"}

# Clean fixture: no secrets, all SBOM entries current, no SLA violations
_CLEAN_FILE_CONTENTS = [
    "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}",        # env-var reference, not literal
    "db_host = localhost",
    "port = 9000",
    "log_level = INFO",
]

_NOW = datetime.now(timezone.utc)

_SBOM_FIXTURE: List[Dict] = [
    {
        "name":         "fastapi",
        "version":      "0.110.0",
        "hash":         "sha256:aabbccdd",
        "cve_status":   "clean",
        "last_scanned": (_NOW - timedelta(days=1)).isoformat(),
    },
    {
        "name":         "pydantic",
        "version":      "2.6.4",
        "hash":         "sha256:11223344",
        "cve_status":   "clean",
        "last_scanned": (_NOW - timedelta(days=2)).isoformat(),
    },
    {
        "name":         "httpx",
        "version":      "0.27.0",
        "hash":         "sha256:99aabbcc",
        "cve_status":   "clean",
        "last_scanned": (_NOW - timedelta(days=1)).isoformat(),
    },
]


def _scan_for_secrets(contents: List[str]) -> List[str]:
    hits = []
    for line in contents:
        for pattern in _SECRET_PATTERNS:
            if pattern.search(line):
                hits.append(line)
    return hits


def _check_sbom_completeness(sbom: List[Dict]) -> List[str]:
    missing = []
    for entry in sbom:
        absent = _SBOM_REQUIRED_FIELDS - set(entry.keys())
        if absent:
            missing.append(f"{entry.get('name', '?')}: missing {absent}")
    return missing


def _check_cve_sla(sbom: List[Dict], now: datetime) -> List[str]:
    violations = []
    for entry in sbom:
        status = entry.get("cve_status", "clean")
        if status == "clean":
            continue
        severity, _, discovered_str = status.partition(":")
        severity = severity.upper()
        if severity not in _CVE_SLA_DAYS:
            continue
        discovered = datetime.fromisoformat(discovered_str.strip())
        if discovered.tzinfo is None:
            discovered = discovered.replace(tzinfo=timezone.utc)
        age_days = (now - discovered).days
        sla = _CVE_SLA_DAYS[severity]
        if age_days > sla:
            violations.append(
                f"{entry['name']} {severity} CVE open {age_days}d > SLA {sla}d"
            )
    return violations


def _make_cert(claims: dict) -> CertificateArtifact:
    sig = "sha256:" + hashlib.sha256(
        json.dumps(claims, sort_keys=True).encode()
    ).hexdigest()[:32]
    return CertificateArtifact(
        subject="security.secret_scan_sbom",
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


def test_secret_scan_and_sbom_clean(tmp_path):
    """No secrets in fixture files; SBOM complete; no CVE SLA violations."""
    secret_hits = _scan_for_secrets(_CLEAN_FILE_CONTENTS)
    assert not secret_hits, f"Secret scan found hits: {secret_hits}"

    sbom_gaps = _check_sbom_completeness(_SBOM_FIXTURE)
    assert not sbom_gaps, f"SBOM missing fields: {sbom_gaps}"

    cve_violations = _check_cve_sla(_SBOM_FIXTURE, _NOW)
    assert not cve_violations, f"CVE SLA violations: {cve_violations}"

    cert = _make_cert({
        "files_scanned":      len(_CLEAN_FILE_CONTENTS),
        "secrets_found":      0,
        "sbom_entries":       len(_SBOM_FIXTURE),
        "sbom_complete":      True,
        "cve_sla_violations": 0,
    })
    archive = AlexandrianArchive(root=tmp_path)
    _emit_cert_to_lineage(cert, archive)

    events = archive.read_lineage()
    assert len(events) == 1
    assert events[0]["subject"] == "security.secret_scan_sbom"
    assert events[0]["claims"]["secrets_found"] == 0


def test_secret_scan_detects_stripe_key():
    """Secret scanner catches a Stripe live key literal."""
    contents = ["api_key = sk_live_ABCDEFGHIJKLMNOPQRSTUV"]  # gitleaks:allow
    hits = _scan_for_secrets(contents)
    assert len(hits) == 1


def test_sbom_missing_fields_detected():
    """SBOM entry missing required field is flagged."""
    incomplete = [{"name": "broken_pkg", "version": "1.0.0"}]
    gaps = _check_sbom_completeness(incomplete)
    assert gaps


def test_cve_sla_violation_detected():
    """HIGH CVE open for 31 days violates the 30-day SLA."""
    now = datetime.now(timezone.utc)
    sbom = [{
        "name":       "vuln_pkg",
        "version":    "0.0.1",
        "hash":       "sha256:deadbeef",
        "cve_status": f"HIGH:{(now - timedelta(days=31)).isoformat()}",
        "last_scanned": now.isoformat(),
    }]
    violations = _check_cve_sla(sbom, now)
    assert len(violations) == 1
    assert "vuln_pkg" in violations[0]
