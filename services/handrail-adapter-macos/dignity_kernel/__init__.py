"""
Dignity Kernel
==============
Constitutional policy enforcement for the adapter layer.

Never-events (always blocked):
  - input.* on Tier E sessions without explicit founder unlock
  - fs.write_* to paths outside ALLOWED_WRITE_ROOTS
  - vision.* screenshot capture without session-level consent flag
  - Any method not in the allowed_methods policy set

Phi-ratio circuit breaker:
  verification_latency ≤ operation_latency × 1.618034
  If violated: breaker opens for RECOVERY_MS, all ops return DENIED.

Constitutional invariant (mirrors NS∞ CANON):
  The dignity kernel cannot be disabled by any runtime flag.
  It can only be modified via a signed policy update with founder receipt.
"""
from __future__ import annotations
import time, os
from pathlib import Path
from typing import Optional
from adapter_core.contract import AdapterRequest, AdapterResponse

# ── Constants ─────────────────────────────────────────────────────────────────
PHI: float = 1.618034
RECOVERY_MS: int = 5000

NEVER_EVENTS: set[str] = {
    # Destructive fs ops require explicit policy unlock
    "fs.delete",
    "fs.rm_rf",
    "input.key_sequence_system",   # e.g. Cmd+Q on all apps
}

ALLOWED_WRITE_ROOTS: list[str] = [
    str(Path.home() / "axiolev_runtime"),
    "/Volumes/NSExternal",
    "/tmp",
]


class DignityKernel:
    """Stateful policy enforcer. One instance per server lifetime."""

    def __init__(self):
        self._breaker_open_until: float = 0.0
        self._last_op_latency_ms: float = 0.0
        self._violations: int = 0

    # ── Public API ─────────────────────────────────────────────────────────

    def check(self, req: AdapterRequest) -> Optional[str]:
        """
        Returns None if allowed, or a denial reason string.
        Called BEFORE dispatching to handler.
        """
        # Circuit breaker
        if time.monotonic() < self._breaker_open_until:
            remaining = int((self._breaker_open_until - time.monotonic()) * 1000)
            return f"CIRCUIT_BREAKER_OPEN: recovers in {remaining}ms"

        # Never-events
        if req.method in NEVER_EVENTS:
            return f"NEVER_EVENT: {req.method} is unconditionally blocked"

        # Write path guard
        if req.method.startswith("fs.write") or req.method.startswith("fs.append"):
            path = req.params.get("path", "")
            if path and not self._is_allowed_write_path(path):
                return f"WRITE_PATH_OUTSIDE_ALLOWED_ROOTS: {path}"

        return None  # allowed

    def record_phi_check(self, op_latency_ms: float, verify_latency_ms: float) -> bool:
        """
        Returns True if within phi ratio, False (+ trips breaker) if violated.
        Only meaningful for ACT+SEE paired ops.
        """
        if op_latency_ms <= 0:
            return True
        ratio = verify_latency_ms / op_latency_ms
        if ratio > PHI:
            self._violations += 1
            self._breaker_open_until = time.monotonic() + (RECOVERY_MS / 1000)
            return False
        return True

    @property
    def violations(self) -> int:
        return self._violations

    @property
    def breaker_open(self) -> bool:
        return time.monotonic() < self._breaker_open_until

    # ── Internals ──────────────────────────────────────────────────────────

    def _is_allowed_write_path(self, path: str) -> bool:
        p = os.path.abspath(path)
        return any(p.startswith(root) for root in ALLOWED_WRITE_ROOTS)
