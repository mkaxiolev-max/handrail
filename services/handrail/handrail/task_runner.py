from __future__ import annotations

import json
import subprocess
from shlex import split as shlex_split
import time
from pathlib import Path
from typing import Any


def _now_ts_ms() -> int:
    return int(time.time() * 1000)


ALLOWED_EXEC_BINARIES = {"pwd", "ls", "cat", "tail", "head", "wc", "find"}
BLOCKED_TOKENS = {";", "&&", "||", ">", ">>", "<", "|", "$(", "`"}


def _validate_exec_command(raw_cmd: str) -> tuple[bool, str | None, list[str] | None]:
    raw_cmd = (raw_cmd or "").strip()
    if not raw_cmd:
        return False, "empty_command", None

    for token in BLOCKED_TOKENS:
        if token in raw_cmd:
            return False, f"blocked_token:{token}", None

    try:
        argv = shlex_split(raw_cmd)
    except Exception:
        return False, "invalid_shell_syntax", None

    if not argv:
        return False, "empty_argv", None

    binary = argv[0]
    if binary not in ALLOWED_EXEC_BINARIES:
        return False, f"unsupported_binary:{binary}", None

    return True, None, argv


def _append_task_event(
    run_dir: Path,
    event_type: str,
    payload: dict[str, Any],
    *,
    service: str = "handrail",
    layer: str = "task_runner",
    status: str = "ok",
    message: str = "",
) -> None:
    seq_path = run_dir / ".task_seq"
    if seq_path.exists():
        try:
            seq = int(seq_path.read_text().strip())
        except Exception:
            seq = 0
    else:
        seq = 0
    seq += 1
    seq_path.write_text(str(seq))

    event = {
        "schema_version": "v1",
        "run_id": payload.get("run_id"),
        "task_id": payload.get("task_id"),
        "event_id": f"evt_{seq:06d}",
        "parent_event_id": None,
        "seq": seq,
        "ts_ms": _now_ts_ms(),
        "mono_ns": time.monotonic_ns(),
        "service": service,
        "layer": layer,
        "event_type": event_type,
        "status": status,
        "policy_hash": payload.get("policy_hash"),
        "message": message or event_type,
        "data": payload,
    }

    ledger_path = run_dir / "proof_ledger.jsonl"
    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")


def _write_run_summary(
    run_dir: Path,
    *,
    run_id: str,
    task_type: str,
    ok: bool,
    rc: int,
    stdout_path: str | None,
    objective: str | None,
    extra: dict[str, Any] | None = None,
) -> None:
    extra = extra or {}
    payload = {
        "schema_version": "v1",
        "run_id": run_id,
        "task_id": f"{task_type}_{run_id}",
        "started_ts_ms": _now_ts_ms(),
        "finished_ts_ms": _now_ts_ms(),
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
        "failure_reason": extra.get("failure_reason"),
        "command": extra.get("command"),
        "snapshot_run_dir": extra.get("snapshot_run_dir"),
        "artifact_refs": sorted([str(p) for p in run_dir.iterdir() if p.is_file()]),
        "event_count": sum(1 for _ in (run_dir / "proof_ledger.jsonl").open()) if (run_dir / "proof_ledger.jsonl").exists() else 0,
        "contradictions": [],
        "stdout_path": stdout_path,
        "rc": rc,
    }

    path = run_dir / "run_summary.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    _append_task_event(
        run_dir,
        "run_summary_written",
        {
            "run_id": run_id,
            "task_id": f"{task_type}_{run_id}",
            "task_type": task_type,
            "ok": ok,
            "rc": rc,
            "checks": payload.get("checks", {}),
        },
        service="handrail",
        layer="ledger",
        status="ok",
        message="Direct task run summary written",
    )


def run_task(
    task_type: str,
    objective: str | None,
    payload: dict[str, Any] | None,
    workspace: Path,
    run_dir: Path,
    run_id: str,
) -> dict[str, Any]:
    payload = payload or {}
    task_id = f"{task_type}_{run_id}"

    _append_task_event(
        run_dir,
        "task_received",
        {
            "run_id": run_id,
            "task_id": task_id,
            "task_type": task_type,
            "objective": objective,
        },
        message="Direct Handrail task received",
    )

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

        _append_task_event(
            run_dir,
            "task_completed",
            {
                "run_id": run_id,
                "task_id": task_id,
                "task_type": task_type,
                "rc": int(p.returncode),
                "boot_go_run_dir": boot_go_run_dir,
                "child_run_dir": child_run_dir,
                "present_state_run_dir": present_state_run_dir,
            },
            status="ok" if p.returncode == 0 else "fail",
            message="Direct boot task completed",
        )

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
            'cd "{}" && curl -sS http://127.0.0.1:8011/healthz && printf "\\n" && curl -sS http://ns:9000/healthz && printf "\\n" && curl -sS http://continuum:8788/state'.format(workspace)
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

        _append_task_event(
            run_dir,
            "task_completed",
            {
                "run_id": run_id,
                "task_id": task_id,
                "task_type": task_type,
                "rc": int(p.returncode),
                "services": services,
            },
            status="ok" if p.returncode == 0 else "fail",
            message="Direct status task completed",
        )

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

        return {
            "ok": p.returncode == 0,
            "task_type": task_type,
            "rc": int(p.returncode),
            "stdout_path": str(run_dir / "stdout.txt"),
        }


    if task_type == "ops_snapshot":
        snapshot_cmd = [
            "bash",
            "-lc",
            'cd "{}" && ./scripts/boot/snapshot.sh'.format(workspace),
        ]
        p = subprocess.run(
            snapshot_cmd,
            cwd=str(workspace),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        (run_dir / "stdout.txt").write_text(p.stdout)

        snapshot_run_dir = None
        for line in p.stdout.splitlines():
            if line.startswith("SNAPSHOT_OK="):
                snapshot_run_dir = line.split("=", 1)[1].strip() or None

        snapshot_ok = bool(snapshot_run_dir)

        _append_task_event(
            run_dir,
            "task_completed",
            {
                "run_id": run_id,
                "task_id": task_id,
                "task_type": task_type,
                "rc": int(p.returncode),
                "snapshot_ok": snapshot_ok,
                "snapshot_run_dir": snapshot_run_dir,
            },
            status="ok" if p.returncode == 0 else "fail",
            message="Direct snapshot task completed",
        )

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
                    "stdout_present": True,
                    "snapshot_ok": snapshot_ok,
                },
                "snapshot_run_dir": snapshot_run_dir,
            },
        )

        return {
            "run_id": run_id,
            "run_dir": str(run_dir),
            "ok": p.returncode == 0,
            "task_type": task_type,
            "rc": int(p.returncode),
            "stdout_path": str(run_dir / "stdout.txt"),
            "snapshot_run_dir": snapshot_run_dir,
        }


    if task_type == "ops_exec_cmd":
        raw_cmd = str((payload or {}).get("cmd") or "").strip()
        ok_cmd, reason, argv = _validate_exec_command(raw_cmd)

        if not ok_cmd:
            msg = reason or "invalid_command"
            (run_dir / "stdout.txt").write_text(msg + "\n", encoding="utf-8")

            _append_task_event(
                run_dir,
                "task_rejected",
                {
                    "run_id": run_id,
                    "task_id": task_id,
                    "task_type": task_type,
                    "cmd": raw_cmd,
                    "reason": msg,
                },
                status="fail",
                message="Exec command rejected",
            )

            _write_run_summary(
                run_dir,
                run_id=run_id,
                task_type=task_type,
                ok=False,
                rc=400,
                stdout_path=str(run_dir / "stdout.txt"),
                objective=objective,
                extra={
                    "checks": {
                        "stdout_present": True,
                        "command_valid": False,
                    },
                    "failure_reason": msg,
                    "command": raw_cmd,
                },
            )

            return {
                "run_id": run_id,
                "run_dir": str(run_dir),
                "ok": False,
                "task_type": task_type,
                "rc": 400,
                "stdout_path": str(run_dir / "stdout.txt"),
                "failure_reason": msg,
            }

        p = subprocess.run(
            argv,
            cwd=str(workspace),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        (run_dir / "stdout.txt").write_text(p.stdout, encoding="utf-8")

        _append_task_event(
            run_dir,
            "task_completed",
            {
                "run_id": run_id,
                "task_id": task_id,
                "task_type": task_type,
                "cmd": raw_cmd,
                "argv": argv,
                "rc": int(p.returncode),
            },
            status="ok" if p.returncode == 0 else "fail",
            message="Direct exec task completed",
        )

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
                    "stdout_present": True,
                    "command_valid": True,
                },
                "command": raw_cmd,
            },
        )

        return {
            "run_id": run_id,
            "run_dir": str(run_dir),
            "ok": p.returncode == 0,
            "task_type": task_type,
            "rc": int(p.returncode),
            "stdout_path": str(run_dir / "stdout.txt"),
            "command": raw_cmd,
        }


    _append_task_event(
        run_dir,
        "task_rejected",
        {
            "run_id": run_id,
            "task_id": task_id,
            "task_type": task_type,
            "supported_task_types": ["ops_boot_check", "ops_status_check", "ops_snapshot", "ops_exec_cmd"],
        },
        status="fail",
        message="Unsupported task type",
    )

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
            "failure_reason": "unsupported_task_type",
        },
    )

    return {
        "ok": False,
        "task_type": task_type,
        "error": "unsupported_task_type",
        "supported_task_types": ["ops_boot_check", "ops_status_check", "ops_snapshot", "ops_exec_cmd"],
    }
