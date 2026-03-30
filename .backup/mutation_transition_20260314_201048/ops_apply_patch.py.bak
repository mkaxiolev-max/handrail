from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

ALLOWED_ROOT = Path("/app")

def _reject_unsafe_patch(patch_text: str) -> str | None:
    lines = patch_text.splitlines()

    for line in lines:
        if line.startswith("--- ") or line.startswith("+++ "):
            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                continue
            target = parts[1].strip()

            if target == "/dev/null":
                continue

            if target.startswith("/"):
                return "absolute_paths_not_allowed"

            normalized = target.removeprefix("a/").removeprefix("b/")
            if ".." in Path(normalized).parts:
                return "parent_path_not_allowed"

    return None

def run_apply_patch(task_request: dict, run_dir: Path) -> dict:
    patch_text = task_request.get("patch")

    if not patch_text:
        return {
            "ok": False,
            "rc": 400,
            "failure_reason": "missing_patch",
            "stdout": "",
            "stderr": "missing_patch",
        }

    unsafe_reason = _reject_unsafe_patch(patch_text)
    if unsafe_reason:
        return {
            "ok": False,
            "rc": 400,
            "failure_reason": unsafe_reason,
            "stdout": "",
            "stderr": unsafe_reason,
        }

    patch_path = Path(run_dir) / "patch.diff"
    patch_path.write_text(patch_text, encoding="utf-8")

    patch_hash = hashlib.sha256(patch_text.encode("utf-8")).hexdigest()

    dry_run = subprocess.run(
        ["patch", "-p1", "--dry-run"],
        input=patch_text,
        cwd=ALLOWED_ROOT,
        capture_output=True,
        text=True,
    )

    (Path(run_dir) / "patch_dry_run_stdout.txt").write_text(dry_run.stdout or "", encoding="utf-8")
    (Path(run_dir) / "patch_dry_run_stderr.txt").write_text(dry_run.stderr or "", encoding="utf-8")

    if dry_run.returncode != 0:
        return {
            "ok": False,
            "rc": dry_run.returncode,
            "failure_reason": "patch_dry_run_failed",
            "patch_hash": patch_hash,
            "stdout": dry_run.stdout or "",
            "stderr": dry_run.stderr or "",
        }

    apply_result = subprocess.run(
        ["patch", "-p1"],
        input=patch_text,
        cwd=ALLOWED_ROOT,
        capture_output=True,
        text=True,
    )

    (Path(run_dir) / "patch_apply_stdout.txt").write_text(apply_result.stdout or "", encoding="utf-8")
    (Path(run_dir) / "patch_apply_stderr.txt").write_text(apply_result.stderr or "", encoding="utf-8")

    return {
        "ok": apply_result.returncode == 0,
        "rc": apply_result.returncode,
        "failure_reason": None if apply_result.returncode == 0 else "patch_apply_failed",
        "patch_hash": patch_hash,
        "stdout": apply_result.stdout or "",
        "stderr": apply_result.stderr or "",
    }
