"""
NS → Handrail CPS Bridge
========================
Drop-in replacement for any NS code that currently uses:
  - subprocess.run(...)
  - os.system(...)
  - shell=True

Usage:
    from ns.handrail_bridge import cps_run, cps_exec

    # Run a named CPS plan from the registry
    result = cps_run("health_check")

    # Run an ad-hoc CPS inline (NS constructs the plan)
    result = cps_exec(
        cps_id="ns_task_001",
        objective="restart monitoring service",
        policy_profile="boot.runtime",
        ops=[
            {"op": "docker.compose_up", "args": {"project_dir": "/workspace", "detached": True}},
            {"op": "http.get", "args": {"url": "http://127.0.0.1:9000/healthz", "timeout_ms": 5000}},
        ],
        expect={"results[1].data.status_code": 200},
    )

    if not result.ok:
        # Classify and handle
        for failure in result.expect_failures:
            print(failure)
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

HANDRAIL_API = os.environ.get("HANDRAIL_API", "http://127.0.0.1:8011")
HANDRAIL_TIMEOUT = int(os.environ.get("HANDRAIL_TIMEOUT_MS", "60000")) / 1000
CPS_DIR = Path(os.environ.get("HANDRAIL_CPS_DIR", "")) or (
    Path(__file__).resolve().parent.parent.parent
    / "handrail" / "handrail" / "cps"
)


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------

@dataclass
class OpResult:
    op_index: int
    op: str
    ok: bool
    data: dict
    signal: Any
    error: str | None
    latency_ms: float
    decision_code: str
    op_digest: str

    @property
    def failed(self) -> bool:
        return not self.ok

    def __repr__(self) -> str:
        status = "✓" if self.ok else "✗"
        return f"[{status}] {self.op} → {self.decision_code} ({self.latency_ms}ms)"


@dataclass
class CPSResult:
    cps_id: str
    ok: bool
    run_id: str
    run_dir: str
    policy_profile: str
    result_digest: str
    ops: list[OpResult] = field(default_factory=list)
    expect_passed: bool = True
    expect_failures: list[dict] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict)

    @property
    def failed(self) -> bool:
        return not self.ok

    @property
    def failure_types(self) -> list[str]:
        return [op.decision_code for op in self.ops if op.failed]

    def assert_ok(self) -> "CPSResult":
        """Raise if not ok — use in boot sequences where failure must halt."""
        if not self.ok:
            codes = self.failure_types
            failures = self.expect_failures
            raise RuntimeError(
                f"CPS {self.cps_id!r} failed. "
                f"decision_codes={codes} expect_failures={failures}"
            )
        return self

    def summary(self) -> dict:
        return {
            "cps_id": self.cps_id,
            "ok": self.ok,
            "run_id": self.run_id,
            "policy_profile": self.policy_profile,
            "expect_passed": self.expect_passed,
            "failure_types": self.failure_types,
            "metrics": self.metrics,
            "digest": self.result_digest[:16] + "...",
        }

    def __repr__(self) -> str:
        status = "OK" if self.ok else "FAIL"
        return f"CPSResult({self.cps_id!r}, {status}, run={self.run_id})"


def _parse_result(raw: dict) -> CPSResult:
    ops = [
        OpResult(
            op_index=r.get("op_index", i),
            op=r.get("op", ""),
            ok=r.get("ok", False),
            data=r.get("data", {}),
            signal=r.get("signal"),
            error=r.get("error"),
            latency_ms=r.get("latency_ms", 0),
            decision_code=r.get("decision_code", "UNKNOWN"),
            op_digest=r.get("op_digest", ""),
        )
        for i, r in enumerate(raw.get("results", []))
    ]
    expect_result = raw.get("expect_result", {})
    return CPSResult(
        cps_id=raw.get("cps_id", ""),
        ok=raw.get("ok", False),
        run_id=raw.get("run_id", ""),
        run_dir=raw.get("run_dir", ""),
        policy_profile=raw.get("policy_profile", "default"),
        result_digest=raw.get("result_digest", ""),
        ops=ops,
        expect_passed=expect_result.get("passed", True),
        expect_failures=expect_result.get("failures", []),
        metrics=raw.get("metrics", {}),
        raw=raw,
    )


# ---------------------------------------------------------------------------
# Core API calls
# ---------------------------------------------------------------------------

def _post_cps(plan: dict, api_base: str = HANDRAIL_API) -> CPSResult:
    try:
        resp = httpx.post(
            f"{api_base}/ops/cps",
            json=plan,
            timeout=HANDRAIL_TIMEOUT,
        )
        resp.raise_for_status()
        return _parse_result(resp.json())
    except httpx.ConnectError:
        raise RuntimeError(
            f"Handrail API unreachable at {api_base}. "
            "Is the container running? Try: docker compose up -d handrail"
        )
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Handrail API error {e.response.status_code}: {e.response.text[:300]}")


def cps_run(cps_id: str, api_base: str = HANDRAIL_API) -> CPSResult:
    """Run a named CPS plan from the registry."""
    plan_path = CPS_DIR / f"{cps_id}.json"
    if not plan_path.exists():
        raise FileNotFoundError(f"CPS plan not found: {cps_id} (looked in {CPS_DIR})")
    plan = json.loads(plan_path.read_text())
    return _post_cps(plan, api_base)


def cps_exec(
    cps_id: str,
    ops: list[dict],
    objective: str | None = None,
    policy_profile: str = "default",
    expect: dict | None = None,
    api_base: str = HANDRAIL_API,
) -> CPSResult:
    """Execute an inline CPS plan constructed by NS."""
    plan = {
        "cps_id": cps_id,
        "objective": objective,
        "ops": ops,
        "expect": expect or {},
        "policy_profile": policy_profile,
    }
    return _post_cps(plan, api_base)


# ---------------------------------------------------------------------------
# Failure classification
# ---------------------------------------------------------------------------

FAILURE_CLASSES = {
    "SERVICE_DOWN": lambda r: any(
        op.decision_code in ("TIMEOUT", "OP_ERROR") and "http" in op.op
        for op in r.ops
    ),
    "POLICY_DENIED": lambda r: any(op.decision_code == "POLICY_DENIED" for op in r.ops),
    "DOCKER_ERROR": lambda r: any(
        op.decision_code == "OP_ERROR" and "docker" in op.op
        for op in r.ops
    ),
    "HEALTHCHECK_FAIL": lambda r: any(
        op.decision_code == "OK" and op.signal not in (200, 0, "ok")
        for op in r.ops
    ),
    "EXPECT_FAIL": lambda r: not r.expect_passed,
    "UNKNOWN_OP": lambda r: any(op.decision_code == "UNKNOWN_OP" for op in r.ops),
}


def classify_failure(result: CPSResult) -> str:
    """Return first matching failure class string."""
    if result.ok:
        return "OK"
    for label, test in FAILURE_CLASSES.items():
        try:
            if test(result):
                return label
        except Exception:
            pass
    return "GENERIC_FAILURE"


# ---------------------------------------------------------------------------
# Golden loop helper
# ---------------------------------------------------------------------------

class GoldenLoop:
    """
    Runs a CPS plan on a fixed interval. Logs every result.
    NS can attach callbacks for failure handling.

    Usage:
        loop = GoldenLoop("health_check", interval_s=30)
        loop.on_failure = lambda r, cls: alert(cls)
        loop.run_forever()
    """

    def __init__(
        self,
        cps_id: str,
        interval_s: int = 30,
        api_base: str = HANDRAIL_API,
        on_failure=None,
        on_success=None,
    ):
        self.cps_id = cps_id
        self.interval_s = interval_s
        self.api_base = api_base
        self.on_failure = on_failure or (lambda r, cls: print(f"[LOOP] FAIL {cls}: {r.summary()}"))
        self.on_success = on_success or (lambda r: print(f"[LOOP] OK {r.cps_id} run={r.run_id}"))
        self._runs: list[CPSResult] = []

    def tick(self) -> CPSResult:
        result = cps_run(self.cps_id, api_base=self.api_base)
        self._runs.append(result)
        if result.ok:
            self.on_success(result)
        else:
            cls = classify_failure(result)
            self.on_failure(result, cls)
        return result

    def run_forever(self) -> None:
        print(f"[GoldenLoop] Starting {self.cps_id!r} every {self.interval_s}s")
        while True:
            try:
                self.tick()
            except Exception as e:
                print(f"[GoldenLoop] Exception: {e}")
            time.sleep(self.interval_s)

    @property
    def last(self) -> CPSResult | None:
        return self._runs[-1] if self._runs else None

    @property
    def consecutive_failures(self) -> int:
        count = 0
        for r in reversed(self._runs):
            if r.failed:
                count += 1
            else:
                break
        return count
