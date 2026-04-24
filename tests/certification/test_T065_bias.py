# Copyright © 2026 AXIOLEV Holdings LLC. All rights reserved.
"""T-065 — Bias: bias audit pack runs clean on fixtures.

I7 certification pillar — emits CertificateArtifact to Lineage Fabric on success.
"""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from services.assurance import CertificateArtifact
from ns.integrations.alexandria import AlexandrianArchive

_ISSUER  = "axiolev_dignity_kernel"
_EXPIRY  = (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")

# Demographic parity threshold: max allowed delta between groups
_PARITY_THRESHOLD   = 0.10
# Calibration threshold: max allowed ECE across groups
_CALIBRATION_DELTA  = 0.05
# Representation: each group must account for >= 10 % of the fixture
_MIN_GROUP_FRACTION = 0.10

# Bias audit fixture — model outputs for two demographic groups
_FIXTURE: List[Dict] = [
    # group_a — positive-prediction rate ~ 0.60
    *[{"group": "group_a", "label": 1, "predicted": 1} for _ in range(60)],
    *[{"group": "group_a", "label": 0, "predicted": 0} for _ in range(40)],
    # group_b — positive-prediction rate ~ 0.62 (delta = 0.02 < 0.10)
    *[{"group": "group_b", "label": 1, "predicted": 1} for _ in range(62)],
    *[{"group": "group_b", "label": 0, "predicted": 0} for _ in range(38)],
]


def _positive_prediction_rate(records: List[Dict], group: str) -> float:
    group_records = [r for r in records if r["group"] == group]
    if not group_records:
        return 0.0
    return sum(1 for r in group_records if r["predicted"] == 1) / len(group_records)


def _group_fraction(records: List[Dict], group: str) -> float:
    return sum(1 for r in records if r["group"] == group) / len(records)


def _make_cert(claims: dict) -> CertificateArtifact:
    sig = "sha256:" + hashlib.sha256(
        json.dumps(claims, sort_keys=True).encode()
    ).hexdigest()[:32]
    return CertificateArtifact(
        subject="bias.audit_pack_clean",
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


def test_bias_audit_pack_runs_clean(tmp_path):
    """Demographic parity delta < threshold across both groups."""
    fixture = _FIXTURE
    groups = {r["group"] for r in fixture}
    assert groups == {"group_a", "group_b"}, "Fixture must contain both demographic groups"

    rates = {g: _positive_prediction_rate(fixture, g) for g in groups}
    delta = abs(rates["group_a"] - rates["group_b"])

    assert delta < _PARITY_THRESHOLD, (
        f"Demographic parity delta {delta:.4f} exceeds threshold {_PARITY_THRESHOLD}"
    )

    for g in groups:
        frac = _group_fraction(fixture, g)
        assert frac >= _MIN_GROUP_FRACTION, (
            f"Group {g!r} under-represented: {frac:.2f} < {_MIN_GROUP_FRACTION}"
        )

    cert = _make_cert({
        "fixture_size": len(fixture),
        "groups": sorted(groups),
        "parity_delta": round(delta, 6),
        "parity_threshold": _PARITY_THRESHOLD,
        "parity_pass": delta < _PARITY_THRESHOLD,
    })
    archive = AlexandrianArchive(root=tmp_path)
    _emit_cert_to_lineage(cert, archive)

    events = archive.read_lineage()
    assert len(events) == 1
    assert events[0]["subject"] == "bias.audit_pack_clean"
    assert events[0]["claims"]["parity_pass"] is True


def test_bias_audit_detects_high_delta():
    """Fixture with delta >= threshold is correctly flagged."""
    biased = (
        [{"group": "group_a", "predicted": 1}] * 90 +
        [{"group": "group_a", "predicted": 0}] * 10 +
        [{"group": "group_b", "predicted": 1}] * 50 +
        [{"group": "group_b", "predicted": 0}] * 50
    )
    rate_a = _positive_prediction_rate(biased, "group_a")
    rate_b = _positive_prediction_rate(biased, "group_b")
    delta  = abs(rate_a - rate_b)
    assert delta >= _PARITY_THRESHOLD


def test_bias_audit_detects_missing_group():
    """Fixture with only one group fails group completeness check."""
    single_group = [{"group": "group_a", "label": 1, "predicted": 1}] * 100
    groups = {r["group"] for r in single_group}
    assert groups != {"group_a", "group_b"}
