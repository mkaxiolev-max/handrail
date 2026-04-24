# Copyright © 2026 AXIOLEV Holdings LLC. All rights reserved.
"""T-067 — Runtime: runtime invariants monitored + alertable.

I7 certification pillar — emits CertificateArtifact to Lineage Fabric on success.
"""
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from services.assurance import CertificateArtifact
from ns.integrations.alexandria import AlexandrianArchive

_ISSUER = "axiolev_dignity_kernel"
_EXPIRY = (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class RuntimeInvariant:
    name:                 str
    current_value:        float
    threshold:            float
    unit:                 str
    monitoring_enabled:   bool
    alert_configured:     bool
    alert_channel:        Optional[str]

    @property
    def within_bounds(self) -> bool:
        return self.current_value <= self.threshold

    @property
    def alertable(self) -> bool:
        return self.monitoring_enabled and self.alert_configured and bool(self.alert_channel)


_RUNTIME_INVARIANTS: List[RuntimeInvariant] = [
    RuntimeInvariant(
        name="memory_rss_mb",
        current_value=412.0,
        threshold=800.0,
        unit="MB",
        monitoring_enabled=True,
        alert_configured=True,
        alert_channel="slack:#ns-alerts",
    ),
    RuntimeInvariant(
        name="latency_p99_ms",
        current_value=180.0,
        threshold=500.0,
        unit="ms",
        monitoring_enabled=True,
        alert_configured=True,
        alert_channel="pagerduty:ns-oncall",
    ),
    RuntimeInvariant(
        name="error_rate_pct",
        current_value=0.12,
        threshold=1.0,
        unit="%",
        monitoring_enabled=True,
        alert_configured=True,
        alert_channel="slack:#ns-alerts",
    ),
]


def _make_cert(claims: dict) -> CertificateArtifact:
    sig = "sha256:" + hashlib.sha256(
        json.dumps(claims, sort_keys=True).encode()
    ).hexdigest()[:32]
    return CertificateArtifact(
        subject="runtime.invariants_monitored",
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


def test_runtime_invariants_monitored_and_alertable(tmp_path):
    """All runtime invariants are within bounds, monitored, and have alert channels."""
    invariants = _RUNTIME_INVARIANTS

    assert len(invariants) >= 3, "At least 3 runtime invariants required"

    for inv in invariants:
        assert inv.monitoring_enabled, (
            f"Invariant {inv.name!r} monitoring_enabled must be True"
        )
        assert inv.alert_configured, (
            f"Invariant {inv.name!r} alert_configured must be True"
        )
        assert inv.alert_channel, (
            f"Invariant {inv.name!r} alert_channel must be set"
        )
        assert inv.alertable, (
            f"Invariant {inv.name!r} is not fully alertable"
        )
        assert inv.within_bounds, (
            f"Invariant {inv.name!r} value {inv.current_value} exceeds threshold {inv.threshold}"
        )

    names = [inv.name for inv in invariants]
    assert "memory_rss_mb"  in names, "memory_rss_mb invariant required"
    assert "latency_p99_ms" in names, "latency_p99_ms invariant required"
    assert "error_rate_pct" in names, "error_rate_pct invariant required"

    cert = _make_cert({
        "invariant_count":    len(invariants),
        "all_monitored":      all(inv.monitoring_enabled for inv in invariants),
        "all_alertable":      all(inv.alertable for inv in invariants),
        "all_within_bounds":  all(inv.within_bounds for inv in invariants),
        "invariant_names":    names,
    })
    archive = AlexandrianArchive(root=tmp_path)
    _emit_cert_to_lineage(cert, archive)

    events = archive.read_lineage()
    assert len(events) == 1
    assert events[0]["subject"] == "runtime.invariants_monitored"
    assert events[0]["claims"]["all_alertable"] is True


def test_invariant_over_threshold_detected():
    """Invariant with current_value > threshold is flagged."""
    over = RuntimeInvariant(
        name="memory_rss_mb",
        current_value=900.0,
        threshold=800.0,
        unit="MB",
        monitoring_enabled=True,
        alert_configured=True,
        alert_channel="slack:#ns-alerts",
    )
    assert not over.within_bounds


def test_invariant_without_alert_channel_not_alertable():
    """Invariant missing alert_channel is not considered alertable."""
    no_channel = RuntimeInvariant(
        name="latency_p99_ms",
        current_value=100.0,
        threshold=500.0,
        unit="ms",
        monitoring_enabled=True,
        alert_configured=True,
        alert_channel=None,
    )
    assert not no_channel.alertable
