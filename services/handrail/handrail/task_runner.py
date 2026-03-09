from __future__ import annotations

import json
import time
import subprocess
from pathlib import Path
from runtime.audit.proof_ledger import append_event
from typing import Any


def _task_id(task_type: str, run_id: str) -> str:
    return f"{task_type}_{run_id}"


def _append_task_event(run_dir: Path, event_type: str, run_id: str, task_type: str, payload: dict, *, message: str, status: str = "ok"):
    append_event(
        run_dir,
        event_type,
        {
            "run_id": run_id,
            "task_id": _task_id(task_type, run_id),
            **payload,
        },
        service="handrail",
        layer="execution",
        status=status,
        message=message,
    )


def _write_run_summary(
    run_dir: Path,
    *,
    run_id: str,
    task_type: str,
    ok: bool,
    rc: int | None,
    stdout_path: str | None,
    objective: str | None,
    extra: dict[str, Any] | None = None,
) -> None:
    extra = extra or {}
    summary = {
        "schema_version": "v1",
        "run_id": run_id,
        "task_id": f"{task_type}_{run_id}",
        "started_ts_ms": int(time.time() * 1000),
        "finished_ts_ms": int(time.time() * 1000),
        "duration_ms": None,
        "ok": ok,
        "intent": objective,
        "task_type": task_type,
        "execution_mode": "direct_handrail_task",
        "policy_version": "v1",
        "policy_hash": None,
        "services": extra.get("services", {}),
        "mounts": extra.get("mounts", {}),
        "checks": extra.get("checks", {}),
        "failure_reason": None if ok else f"rc_{rc}",
        "artifact_refs": sorted(
            str(p) for p in run_dir.iterdir() if p.is_file()
        ) if run_dir.exists() else [],
        "event_count": 0,
        "contradictions": [],
        "stdout_path": stdout_path,
        "rc": rc,
    }
    (run_dir / "run_summary.json").write_text(json.dumps(summary, indent=2))


def run_task(task_type: str, objective: str | None, payload: dict[str, Any] | None, workspace: Path, run_dir: Path, run_id: str) -> dict[str, Any]:
    payload = payload or {}

    _append_task_event(
        run_dir,
        "task_received",
        run_id,
        task_type,
        {
            "objective": objective,
            "payload": payload,
        },
        message=f"Task received: {task_type}",
    )
    run_id = run_dir.name

    if task_type == "ops_boot_check":
        governed_script = workspace / "scripts" / "boot" / "boot_go.sh"
        cmd = ["bash", "-lc", f'cd "{workspace}" && bash "{governed_script}"']
        p = subprocess.run(
            cmd,
            cwd=str(workspace),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        (run_dir / "stdout.txt").write_text(p.stdout)

        boot_go_run_dir = None
        child_run_dir = None
        present_state_run_dir = None
        for line in p.stdout.splitlines():
            if line.startswith("BOOT_GO_RUN_DIR="):
                boot_go_run_dir = line.split("=", 1)[1].strip()
            elif line.startswith("CHILD_RUN_DIR="):
                child_run_dir = line.split("=", 1)[1].strip()
            elif line.startswith("PRESENT_STATE_RUN="):
                present_state_run_dir = line.split("=", 1)[1].strip()

        _write_run_summary(
            run_dir,
            run_id=run_id,
            task_type=task_type,
            ok=(p.returncode == 0),
            rc=int(p.returncode),
            stdout_path=str(run_dir / "stdout.txt"),
            objective=objective,
            extra={
                "checks": {
                    "boot_go_stdout_present": True,
                }
            },
        )

        _append_task_event(
            run_dir,
            "task_completed",
            run_id,
            task_type,
            {
                "rc": int(p.returncode),
                "stdout_path": str(run_dir / "stdout.txt"),
                "boot_go_run_dir": boot_go_run_dir,
                "child_run_dir": child_run_dir,
                "present_state_run_dir": present_state_run_dir,
            },
            message=f"Task completed: {task_type}",
            status="ok" if p.returncode == 0 else "fail",
        )

        return {
            "ok": p.returncode == 0,
            "task_type": task_type,
            "rc": int(p.returncode),
            "stdout_path": str(run_dir / "stdout.txt"),
            "boot_go_run_dir": boot_go_run_dir,
            "child_run_dir": child_run_dir,
            "present_state_run_dir": present_state_run_dir,
        }

    if task_type == "ops_status_check":
        status_cmd = [
            "bash",
            "-lc",
            'cd "{}" && curl -sS http://127.0.0.1:8011/v1/status && printf "\\n" && curl -sS http://ns:9000/healthz && printf "\\n" && curl -sS http://continuum:8788/state'.format(workspace)
        ]
        p = subprocess.run(
            status_cmd,
            cwd=str(workspace),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        (run_dir / "stdout.txt").write_text(p.stdout)

        services = {
            "handrail": "ok" if '"ok":true' in p.stdout or '"ok": true' in p.stdout else "unknown",
            "ns": "ok" if '"status":"ok"' in p.stdout or '"status": "ok"' in p.stdout else "unknown",
            "continuum": "ok" if '"global_tier"' in p.stdout else "unknown",
        }

        _write_run_summary(
            run_dir,
            run_id=run_id,
            task_type=task_type,
            ok=(p.returncode == 0),
            rc=int(p.returncode),
            stdout_path=str(run_dir / "stdout.txt"),
            objective=objective,
            extra={
                "services": services,
                "checks": {
                    "stdout_present": True,
                },
            },
        )

        _append_task_event(
            run_dir,
            "task_completed",
            run_id,
            task_type,
            {
                "rc": int(p.returncode),
                "stdout_path": str(run_dir / "stdout.txt"),
                "services": services,
            },
            message=f"Task completed: {task_type}",
            status="ok" if p.returncode == 0 else "fail",
        )

        return {
            "ok": p.returncode == 0,
            "task_type": task_type,
            "rc": int(p.returncode),
            "stdout_path": str(run_dir / "stdout.txt"),
        }

    _write_run_summary(
        run_dir,
        run_id=run_id,
        task_type=task_type,
        ok=False,
        rc=400,
        stdout_path=None,
        objective=objective,
        extra={
            "checks": {
                "supported_task_types": False,
            },
        },
    )

    _append_task_event(
        run_dir,
        "task_completed",
        run_id,
        task_type,
        {
            "error": "unsupported_task_type",
            "supported_task_types": ["ops_boot_check", "ops_status_check"],
        },
        message=f"Task rejected: {task_type}",
        status="fail",
    )

    return {
        "ok": False,
        "task_type": task_type,
        "error": "unsupported_task_type",
        "supported_task_types": ["ops_boot_check", "ops_status_check"],
    }
