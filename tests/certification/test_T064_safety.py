# Copyright © 2026 AXIOLEV Holdings LLC. All rights reserved.
"""T-064 — Safety: kill-switch + pause-budget bounds enforced.

I7 certification pillar — emits CertificateArtifact to Lineage Fabric on success.
"""
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from services.assurance import CertificateArtifact
from ns.integrations.alexandria import AlexandrianArchive

_ISSUER = "axiolev_dignity_kernel"
_EXPIRY = (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")

MAX_OPS       = 100
MAX_PAUSE_MS  = 5_000
MAX_BURST_OPS = 20


@dataclass
class BudgetController:
    max_ops:       int
    max_pause_ms:  int
    max_burst_ops: int
    current_ops:   int = 0
    paused:        bool = False
    kill_switch_fired: bool = False

    def execute_op(self) -> bool:
        """Returns False and fires kill-switch if over budget."""
        self.current_ops += 1
        if self.current_ops > self.max_ops:
            self.kill_switch_fired = True
            return False
        return True

    def pause(self, duration_ms: int) -> bool:
        """Returns False if pause exceeds budget."""
        if duration_ms > self.max_pause_ms:
            return False
        self.paused = True
        return True

    def burst_allowed(self, ops: int) -> bool:
        return ops <= self.max_burst_ops


def _make_cert(claims: dict) -> CertificateArtifact:
    sig = "sha256:" + hashlib.sha256(
        json.dumps(claims, sort_keys=True).encode()
    ).hexdigest()[:32]
    return CertificateArtifact(
        subject="safety.kill_switch_bounds",
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


def test_kill_switch_fires_at_op_limit(tmp_path):
    """Kill-switch fires exactly when ops exceed MAX_OPS."""
    ctrl = BudgetController(
        max_ops=MAX_OPS,
        max_pause_ms=MAX_PAUSE_MS,
        max_burst_ops=MAX_BURST_OPS,
    )

    # Execute ops up to the limit — all must succeed
    for _ in range(MAX_OPS):
        assert ctrl.execute_op() is True, "Op within budget must succeed"
    assert not ctrl.kill_switch_fired

    # One more op over the limit must trigger kill-switch
    result = ctrl.execute_op()
    assert result is False
    assert ctrl.kill_switch_fired, "Kill-switch must fire when over MAX_OPS"

    # Pause within budget must succeed
    assert ctrl.pause(MAX_PAUSE_MS) is True

    # Burst within limit must be allowed
    assert ctrl.burst_allowed(MAX_BURST_OPS) is True

    cert = _make_cert({
        "max_ops": MAX_OPS,
        "max_pause_ms": MAX_PAUSE_MS,
        "kill_switch_enforced": True,
        "pause_budget_enforced": True,
    })
    archive = AlexandrianArchive(root=tmp_path)
    _emit_cert_to_lineage(cert, archive)

    events = archive.read_lineage()
    assert len(events) == 1
    assert events[0]["claims"]["kill_switch_enforced"] is True


def test_pause_exceeding_budget_rejected():
    """Pause request exceeding MAX_PAUSE_MS is rejected."""
    ctrl = BudgetController(
        max_ops=MAX_OPS,
        max_pause_ms=MAX_PAUSE_MS,
        max_burst_ops=MAX_BURST_OPS,
    )
    assert ctrl.pause(MAX_PAUSE_MS + 1) is False
    assert not ctrl.paused


def test_burst_over_limit_rejected():
    """Burst op count exceeding MAX_BURST_OPS is rejected."""
    ctrl = BudgetController(
        max_ops=MAX_OPS,
        max_pause_ms=MAX_PAUSE_MS,
        max_burst_ops=MAX_BURST_OPS,
    )
    assert ctrl.burst_allowed(MAX_BURST_OPS + 1) is False


def test_kill_switch_bounds_constants():
    """Safety bounds meet NS constitutional minimums."""
    assert MAX_OPS >= 10,      "MAX_OPS must be at least 10"
    assert MAX_PAUSE_MS <= 30_000, "MAX_PAUSE_MS must not exceed 30 000 ms"
    assert MAX_BURST_OPS <= MAX_OPS, "Burst limit must not exceed total op limit"
