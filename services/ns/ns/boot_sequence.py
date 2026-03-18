"""
NS Boot Sequence — CPS-driven
==============================
Replaces any NS boot logic that used subprocess/shell.

All boot steps go through Handrail /ops/cps.
No shell execution. No subprocess.run. No os.system.

Boot phases:
  Phase 0 — Preflight (Handrail API alive?)
  Phase 1 — Stack up (docker.compose_up)
  Phase 2 — Health verify (http.get all services)
  Phase 3 — Repo state (git.status + git.log)
  Phase 4 — NS ready signal

Each phase produces a CPSResult with full evidence.
Boot halts on any phase failure unless skip_on_failure=True.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from ns.handrail_bridge import CPSResult, classify_failure, cps_exec, cps_run


# ---------------------------------------------------------------------------
# Boot config
# ---------------------------------------------------------------------------

@dataclass
class BootConfig:
    workspace: str = "/workspace"
    handrail_port: int = 8011
    ns_port: int = 9000
    continuum_port: int = 8788
    healthcheck_timeout_ms: int = 5000
    compose_build: bool = False
    skip_compose_up: bool = False        # set True if containers already running


# ---------------------------------------------------------------------------
# Boot result
# ---------------------------------------------------------------------------

@dataclass
class BootResult:
    ok: bool
    phases: list[dict] = field(default_factory=list)
    failure_phase: str | None = None
    failure_class: str | None = None

    def summary(self) -> dict:
        return {
            "ok": self.ok,
            "phases_run": len(self.phases),
            "failure_phase": self.failure_phase,
            "failure_class": self.failure_class,
            "phase_results": [
                {"phase": p["phase"], "ok": p["ok"], "digest": p.get("digest", "")[:12] + "..."}
                for p in self.phases
            ],
        }


# ---------------------------------------------------------------------------
# Boot sequence
# ---------------------------------------------------------------------------

def boot(config: BootConfig | None = None) -> BootResult:
    cfg = config or BootConfig()
    result = BootResult(ok=False)

    print("[NS BOOT] Starting CPS-driven boot sequence")

    # ------------------------------------------------------------------
    # Phase 0: Preflight — is Handrail API alive?
    # ------------------------------------------------------------------
    print("[NS BOOT] Phase 0: Preflight")
    try:
        preflight = cps_exec(
            cps_id="ns_preflight",
            objective="verify Handrail API is reachable before boot",
            policy_profile="readonly.local",
            ops=[
                {"op": "http.get", "args": {
                    "url": f"http://127.0.0.1:{cfg.handrail_port}/healthz",
                    "timeout_ms": 3000,
                }},
            ],
            expect={f"results[0].data.status_code": 200},
        )
    except RuntimeError as e:
        result.failure_phase = "preflight"
        result.failure_class = "HANDRAIL_UNREACHABLE"
        print(f"[NS BOOT] ABORT — Handrail not reachable: {e}")
        return result

    _record_phase(result, "preflight", preflight)
    if not preflight.ok:
        result.failure_phase = "preflight"
        result.failure_class = classify_failure(preflight)
        print(f"[NS BOOT] ABORT — Preflight failed: {result.failure_class}")
        return result
    print("[NS BOOT] Phase 0: OK")

    # ------------------------------------------------------------------
    # Phase 1: Stack up
    # ------------------------------------------------------------------
    if not cfg.skip_compose_up:
        print("[NS BOOT] Phase 1: Stack up")
        stack_up = cps_exec(
            cps_id="ns_stack_up",
            objective="bring up NS docker stack",
            policy_profile="boot.runtime",
            ops=[
                {"op": "docker.compose_up", "args": {
                    "project_dir": cfg.workspace,
                    "detached": True,
                    "build": cfg.compose_build,
                }},
            ],
            expect={},
        )
        _record_phase(result, "stack_up", stack_up)
        if not stack_up.ok:
            result.failure_phase = "stack_up"
            result.failure_class = classify_failure(stack_up)
            print(f"[NS BOOT] ABORT — Stack up failed: {result.failure_class}")
            return result
        print("[NS BOOT] Phase 1: OK — waiting for services to settle")
        time.sleep(3)
    else:
        print("[NS BOOT] Phase 1: Skipped (skip_compose_up=True)")

    # ------------------------------------------------------------------
    # Phase 2: Health verify
    # ------------------------------------------------------------------
    print("[NS BOOT] Phase 2: Health verify")
    health = cps_exec(
        cps_id="ns_health_verify",
        objective="verify all NS services are healthy post-boot",
        policy_profile="readonly.local",
        ops=[
            {"op": "http.get", "args": {
                "url": f"http://127.0.0.1:{cfg.handrail_port}/healthz",
                "timeout_ms": cfg.healthcheck_timeout_ms,
            }},
            {"op": "http.get", "args": {
                "url": f"http://127.0.0.1:{cfg.ns_port}/healthz",
                "timeout_ms": cfg.healthcheck_timeout_ms,
            }},
            {"op": "http.get", "args": {
                "url": f"http://127.0.0.1:{cfg.continuum_port}/state",
                "timeout_ms": cfg.healthcheck_timeout_ms,
            }},
        ],
        expect={
            "results[0].data.status_code": 200,
            "results[1].data.status_code": 200,
            "results[2].data.status_code": 200,
        },
    )
    _record_phase(result, "health_verify", health)
    if not health.ok:
        result.failure_phase = "health_verify"
        result.failure_class = classify_failure(health)
        print(f"[NS BOOT] ABORT — Health verify failed: {result.failure_class}")
        _print_health_detail(health)
        return result
    print("[NS BOOT] Phase 2: OK — all services healthy")

    # ------------------------------------------------------------------
    # Phase 3: Repo state
    # ------------------------------------------------------------------
    print("[NS BOOT] Phase 3: Repo state")
    repo = cps_exec(
        cps_id="ns_repo_state",
        objective="capture repo state at boot time",
        policy_profile="repo.inspect",
        ops=[
            {"op": "git.status", "args": {"repo": cfg.workspace}},
            {"op": "git.log", "args": {"repo": cfg.workspace, "limit": 3, "oneline": True}},
        ],
        expect={},
    )
    _record_phase(result, "repo_state", repo)
    # Repo state is informational — don't halt on failure
    if not repo.ok:
        print(f"[NS BOOT] WARNING — Repo state capture failed (non-fatal): {classify_failure(repo)}")
    else:
        git_status = repo.ops[0].data if repo.ops else {}
        clean = git_status.get("clean", False)
        print(f"[NS BOOT] Phase 3: OK — repo {'clean' if clean else 'has uncommitted changes'}")

    # ------------------------------------------------------------------
    # Phase 4: Ready
    # ------------------------------------------------------------------
    print("[NS BOOT] Phase 4: NS ready")
    result.ok = True
    print("[NS BOOT] ✅ Boot complete")
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _record_phase(boot_result: BootResult, phase: str, cps_result: CPSResult) -> None:
    boot_result.phases.append({
        "phase": phase,
        "ok": cps_result.ok,
        "run_id": cps_result.run_id,
        "digest": cps_result.result_digest,
        "failure_class": classify_failure(cps_result) if not cps_result.ok else None,
    })


def _print_health_detail(health: CPSResult) -> None:
    for op in health.ops:
        status = "✓" if op.ok else "✗"
        print(f"  {status} {op.op}: signal={op.signal} code={op.decision_code} err={op.error}")
    for f in health.expect_failures:
        print(f"  EXPECT FAIL: {f}")
