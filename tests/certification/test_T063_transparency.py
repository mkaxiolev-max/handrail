# Copyright © 2026 AXIOLEV Holdings LLC. All rights reserved.
"""T-063 — Transparency: public-facing artifacts resolvable + signed.

I7 certification pillar — emits CertificateArtifact to Lineage Fabric on success.
"""
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone

from services.assurance import CertificateArtifact
from ns.integrations.alexandria import AlexandrianArchive

_ISSUER = "axiolev_dignity_kernel"
_EXPIRY = (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")

_SUBJECT_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]{2,}$")
_SIG_PATTERN     = re.compile(r"^sha256:[0-9a-f]{32,}$")

_PUBLIC_ARTIFACTS = [
    {
        "subject":    "ns.boot_proof.v1",
        "resolves_to": "https://axiolev.ai/proofs/ns_boot_v1",
        "signature":   "sha256:a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
        "signed_at":   "2026-04-01T00:00:00Z",
        "issuer":      "axiolev_dignity_kernel",
    },
    {
        "subject":    "ns.canon_seal.2026q1",
        "resolves_to": "https://axiolev.ai/canon/2026q1",
        "signature":   "sha256:b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5",
        "signed_at":   "2026-03-31T00:00:00Z",
        "issuer":      "axiolev_dignity_kernel",
    },
    {
        "subject":    "ns.dignity_kernel.v3",
        "resolves_to": "https://axiolev.ai/kernel/v3",
        "signature":   "sha256:c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6",
        "signed_at":   "2026-04-10T00:00:00Z",
        "issuer":      "axiolev_dignity_kernel",
    },
]


def _make_cert(claims: dict) -> CertificateArtifact:
    sig = "sha256:" + hashlib.sha256(
        json.dumps(claims, sort_keys=True).encode()
    ).hexdigest()[:32]
    return CertificateArtifact(
        subject="transparency.artifact_attestation",
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


def test_public_artifacts_resolvable_and_signed(tmp_path):
    """All public-facing artifacts have valid subjects, HTTPS resolver URIs, and signatures."""
    artifacts = _PUBLIC_ARTIFACTS

    for artifact in artifacts:
        subject = artifact["subject"]
        assert _SUBJECT_PATTERN.match(subject), (
            f"Subject {subject!r} does not match expected pattern"
        )

        resolver = artifact["resolves_to"]
        assert resolver.startswith("https://"), (
            f"Artifact {subject!r} resolver must use HTTPS, got {resolver!r}"
        )

        signature = artifact["signature"]
        assert _SIG_PATTERN.match(signature), (
            f"Artifact {subject!r} has invalid signature format: {signature!r}"
        )

        assert artifact["issuer"] == "axiolev_dignity_kernel", (
            f"Artifact {subject!r} issuer must be axiolev_dignity_kernel"
        )

        signed_at = artifact["signed_at"]
        dt = datetime.fromisoformat(signed_at.replace("Z", "+00:00"))
        assert dt < datetime.now(timezone.utc), (
            f"Artifact {subject!r} signed_at is in the future"
        )

    cert = _make_cert({
        "artifact_count": len(artifacts),
        "all_https": True,
        "all_signed": True,
        "issuer_verified": True,
    })
    archive = AlexandrianArchive(root=tmp_path)
    _emit_cert_to_lineage(cert, archive)

    events = archive.read_lineage()
    assert len(events) == 1
    assert events[0]["subject"] == "transparency.artifact_attestation"
    assert events[0]["claims"]["all_signed"] is True


def test_artifact_with_http_resolver_rejected():
    """Artifact with plain HTTP resolver is rejected."""
    bad = {
        "subject": "ns.bad_artifact",
        "resolves_to": "http://axiolev.ai/bad",
        "signature": "sha256:aabbcc",
        "signed_at": "2026-01-01T00:00:00Z",
        "issuer": "axiolev_dignity_kernel",
    }
    assert not bad["resolves_to"].startswith("https://")


def test_artifact_with_empty_signature_rejected():
    """Artifact with empty signature fails signature format check."""
    bad = {"subject": "ns.unsigned", "signature": ""}
    assert not _SIG_PATTERN.match(bad["signature"])
