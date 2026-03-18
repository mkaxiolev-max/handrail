"""
NS Golden Loops
===============
Three autonomous monitoring loops, all CPS-driven.

Loop 1: health_check    — every 30s, verifies service endpoints
Loop 2: ns_boot_verify  — every 60s, ensures system remains boot-clean
Loop 3: repo_inspect    — every 120s, ensures code state

All loops produce CPS evidence. All failures are classified.
Alert hooks are pluggable (log, webhook, SMS via Twilio).

Usage:
    from ns.golden_loops import start_all_loops
    start_all_loops()  # runs in background threads

Or individually:
    from ns.golden_loops import HealthLoop
    loop = HealthLoop()
    loop.start()
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone

from ns.handrail_bridge import CPSResult, GoldenLoop, classify_failure


# ---------------------------------------------------------------------------
# Alert dispatcher (pluggable)
# ---------------------------------------------------------------------------

class AlertDispatcher:
    """Override alert methods or attach handlers."""

    def on_failure(self, loop_name: str, result: CPSResult, failure_class: str) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        print(f"[ALERT][{ts}] {loop_name} FAIL — class={failure_class} cps={result.cps_id} run={result.run_id}")
        for op in result.ops:
            if op.failed:
                print(f"  ✗ {op.op}: {op.decision_code} — {op.error}")

    def on_recovery(self, loop_name: str, result: CPSResult) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        print(f"[RECOVERY][{ts}] {loop_name} recovered — run={result.run_id}")

    def on_consecutive_failures(self, loop_name: str, count: int, result: CPSResult) -> None:
        """Called when consecutive failure threshold is crossed."""
        print(f"[CRITICAL][{loop_name}] {count} consecutive failures — class={classify_failure(result)}")


_default_alert = AlertDispatcher()


# ---------------------------------------------------------------------------
# Loop wrappers with state tracking
# ---------------------------------------------------------------------------

class TrackedLoop:
    def __init__(
        self,
        name: str,
        cps_id: str,
        interval_s: int,
        alert: AlertDispatcher | None = None,
        consecutive_failure_threshold: int = 3,
    ):
        self.name = name
        self.cps_id = cps_id
        self.interval_s = interval_s
        self.alert = alert or _default_alert
        self.threshold = consecutive_failure_threshold
        self._was_ok: bool | None = None
        self._thread: threading.Thread | None = None

        self._loop = GoldenLoop(
            cps_id=cps_id,
            interval_s=interval_s,
            on_success=self._handle_success,
            on_failure=self._handle_failure,
        )

    def _handle_success(self, result: CPSResult) -> None:
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        print(f"[{ts}][{self.name}] OK run={result.run_id} {result.metrics.get('duration_ms', '?')}ms")
        # Recovery detection
        if self._was_ok is False:
            self.alert.on_recovery(self.name, result)
        self._was_ok = True

    def _handle_failure(self, result: CPSResult, failure_class: str) -> None:
        self.alert.on_failure(self.name, result, failure_class)
        self._was_ok = False
        if self._loop.consecutive_failures >= self.threshold:
            self.alert.on_consecutive_failures(self.name, self._loop.consecutive_failures, result)

    def start(self, daemon: bool = True) -> "TrackedLoop":
        self._thread = threading.Thread(
            target=self._loop.run_forever,
            name=f"loop-{self.name}",
            daemon=daemon,
        )
        self._thread.start()
        print(f"[{self.name}] Loop started (interval={self.interval_s}s, cps={self.cps_id})")
        return self

    def tick(self) -> CPSResult:
        """Single synchronous tick — useful for testing."""
        return self._loop.tick()

    @property
    def last(self) -> CPSResult | None:
        return self._loop.last

    @property
    def consecutive_failures(self) -> int:
        return self._loop.consecutive_failures


# ---------------------------------------------------------------------------
# The three golden loops
# ---------------------------------------------------------------------------

class HealthLoop(TrackedLoop):
    """Loop 1: Service health — 30s interval."""
    def __init__(self, alert: AlertDispatcher | None = None):
        super().__init__(
            name="health",
            cps_id="health_check",
            interval_s=30,
            alert=alert,
            consecutive_failure_threshold=3,
        )


class BootVerifyLoop(TrackedLoop):
    """Loop 2: Boot verify — 60s interval."""
    def __init__(self, alert: AlertDispatcher | None = None):
        super().__init__(
            name="boot_verify",
            cps_id="ns_boot_v1",
            interval_s=60,
            alert=alert,
            consecutive_failure_threshold=2,
        )


class RepoInspectLoop(TrackedLoop):
    """Loop 3: Repo state — 120s interval."""
    def __init__(self, alert: AlertDispatcher | None = None):
        super().__init__(
            name="repo_inspect",
            cps_id="repo_inspect",
            interval_s=120,
            alert=alert,
            consecutive_failure_threshold=5,
        )


# ---------------------------------------------------------------------------
# Start all
# ---------------------------------------------------------------------------

def start_all_loops(
    alert: AlertDispatcher | None = None,
    block: bool = False,
) -> tuple[HealthLoop, BootVerifyLoop, RepoInspectLoop]:
    """
    Start all three golden loops in background daemon threads.
    If block=True, sleeps forever (useful as main entrypoint).
    """
    health = HealthLoop(alert=alert).start()
    boot = BootVerifyLoop(alert=alert).start()
    repo = RepoInspectLoop(alert=alert).start()

    if block:
        print("[GoldenLoops] All loops running. Ctrl+C to stop.")
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            print("[GoldenLoops] Stopped.")

    return health, boot, repo


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    start_all_loops(block=True)
