from __future__ import annotations

import json
import time
from pathlib import Path

def _child_run_id(parent_run_dir: Path, idx: int, task_type: str) -> str:
    safe_task = task_type.replace("/", "_").replace(" ", "_")
    return f"{parent_run_dir.name}_step_{idx:02d}_{safe_task}_{int(time.time() * 1000)}"

def execute_plan(task_request: dict, run_dir: Path, task_runner):
    steps = task_request.get("steps")

    if not isinstance(steps, list) or not steps:
        return {
            "ok": False,
            "rc": 400,
            "failure_reason": "missing_steps",
            "results": [],
        }

    allowed_tasks = {
        "ops_apply_patch",
        "ops_run_tests",
        "ops_snapshot",
    }

    results = []
    children_root = Path(run_dir) / "children"
    children_root.mkdir(parents=True, exist_ok=True)

    for idx, step in enumerate(steps, start=1):
        task_type = step.get("task")
        payload = step.get("payload", {})
        objective = step.get("objective", "")

        if task_type not in allowed_tasks:
            return {
                "ok": False,
                "rc": 400,
                "failure_reason": f"unsupported_plan_task:{task_type}",
                "failed_step": task_type,
                "results": results,
            }

        child_run_id = _child_run_id(Path(run_dir), idx, task_type)
        child_run_dir = children_root / child_run_id
        child_run_dir.mkdir(parents=True, exist_ok=True)

        result = task_runner(
            task_type=task_type,
            objective=objective,
            payload=payload,
            workspace=Path("/app"),
            run_dir=child_run_dir,
            run_id=child_run_id,
        )

        results.append(
            {
                "index": idx,
                "task": task_type,
                "objective": objective,
                "child_run_id": child_run_id,
                "child_run_dir": str(child_run_dir),
                "result": result,
            }
        )

        if not result.get("ok", False):
            return {
                "ok": False,
                "rc": result.get("rc", 1),
                "failure_reason": result.get("failure_reason", "plan_step_failed"),
                "failed_step": task_type,
                "results": results,
            }

    return {
        "ok": True,
        "rc": 0,
        "failure_reason": None,
        "results": results,
    }
