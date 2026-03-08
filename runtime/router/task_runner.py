from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict


def run_task(task_type: str, objective: str | None, payload: dict[str, Any] | None, workspace: Path, run_dir: Path) -> dict[str, Any]:
    payload = payload or {}

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
            'cd "{}" && curl -sS http://127.0.0.1:8011/v1/status && printf "\\n" && curl -sS http://127.0.0.1:9000/healthz && printf "\\n" && curl -sS http://127.0.0.1:8788/state'.format(workspace)
        ]
        p = subprocess.run(
            status_cmd,
            cwd=str(workspace),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        (run_dir / "stdout.txt").write_text(p.stdout)

        return {
            "ok": p.returncode == 0,
            "task_type": task_type,
            "rc": int(p.returncode),
            "stdout_path": str(run_dir / "stdout.txt"),
        }

    return {
        "ok": False,
        "task_type": task_type,
        "error": "unsupported_task_type",
        "supported_task_types": ["ops_boot_check", "ops_status_check"],
    }
