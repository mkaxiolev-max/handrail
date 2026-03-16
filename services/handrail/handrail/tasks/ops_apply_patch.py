from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ALLOWED_ROOT = Path("/app")


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return _sha256_bytes(path.read_bytes())


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


def _extract_target_files(patch_text: str) -> list[str]:
    files: list[str] = []
    seen: set[str] = set()

    for line in patch_text.splitlines():
        if not (line.startswith("--- ") or line.startswith("+++ ")):
            continue

        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue

        target = parts[1].strip()
        if target == "/dev/null":
            continue

        normalized = target.removeprefix("a/").removeprefix("b/")
        if normalized not in seen:
            seen.add(normalized)
            files.append(normalized)

    return files


def _file_state(path_str: str) -> dict:
    p = ALLOWED_ROOT / path_str
    exists = p.exists()
    is_file = p.is_file()

    return {
        "path": path_str,
        "exists": exists,
        "is_file": is_file,
        "size": p.stat().st_size if exists and is_file else None,
        "sha256": _sha256_file(p) if exists and is_file else None,
    }


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def run_apply_patch(task_request: dict, run_dir: Path) -> dict:
    patch_text = task_request.get("patch")

    if not patch_text:
        return {
            "ok": False,
            "rc": 400,
            "failure_reason": "missing_patch",
            "stdout": "",
            "stderr": "missing_patch",
            "patch_hash": None,
            "target_files": [],
            "apply_rc": 400,
        }

    unsafe_reason = _reject_unsafe_patch(patch_text)
    if unsafe_reason:
        return {
            "ok": False,
            "rc": 400,
            "failure_reason": unsafe_reason,
            "stdout": "",
            "stderr": unsafe_reason,
            "patch_hash": _sha256_bytes(patch_text.encode("utf-8")),
            "target_files": _extract_target_files(patch_text),
            "apply_rc": 400,
        }

    patch_path = Path(run_dir) / "patch.diff"
    patch_path.write_text(patch_text, encoding="utf-8")

    patch_hash = _sha256_bytes(patch_text.encode("utf-8"))
    target_files = _extract_target_files(patch_text)

    state_before = {
        "target_files": [_file_state(path_str) for path_str in target_files],
    }
    _write_json(Path(run_dir) / "state_before.json", state_before)

    simulated_transition = {
        "patch_hash": patch_hash,
        "target_files": target_files,
        "target_file_count": len(target_files),
    }
    _write_json(Path(run_dir) / "simulated_transition.json", simulated_transition)

    try:
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
            actual_delta = {
                "apply_rc": dry_run.returncode,
                "files_changed": [],
                "dry_run_only": True,
            }
            _write_json(Path(run_dir) / "actual_delta.json", actual_delta)

            state_after = {
                "target_files": [_file_state(path_str) for path_str in target_files],
            }
            _write_json(Path(run_dir) / "state_after.json", state_after)

            return {
                "ok": False,
                "rc": dry_run.returncode,
                "failure_reason": "patch_dry_run_failed",
                "patch_hash": patch_hash,
                "target_files": target_files,
                "apply_rc": dry_run.returncode,
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

        state_after = {
            "target_files": [_file_state(path_str) for path_str in target_files],
        }
        _write_json(Path(run_dir) / "state_after.json", state_after)

        before_by_path = {x["path"]: x for x in state_before["target_files"]}
        after_by_path = {x["path"]: x for x in state_after["target_files"]}

        files_changed = []
        for path_str in target_files:
            before = before_by_path.get(path_str, {})
            after = after_by_path.get(path_str, {})
            if (
                before.get("sha256") != after.get("sha256")
                or before.get("exists") != after.get("exists")
                or before.get("size") != after.get("size")
            ):
                files_changed.append(
                    {
                        "path": path_str,
                        "before_exists": before.get("exists"),
                        "after_exists": after.get("exists"),
                        "before_sha256": before.get("sha256"),
                        "after_sha256": after.get("sha256"),
                        "before_size": before.get("size"),
                        "after_size": after.get("size"),
                    }
                )

        actual_delta = {
            "apply_rc": apply_result.returncode,
            "patch_hash": patch_hash,
            "target_files": target_files,
            "files_changed": files_changed,
        }
        _write_json(Path(run_dir) / "actual_delta.json", actual_delta)

        return {
            "ok": apply_result.returncode == 0,
            "rc": apply_result.returncode,
            "failure_reason": None if apply_result.returncode == 0 else "patch_apply_failed",
            "patch_hash": patch_hash,
            "target_files": target_files,
            "apply_rc": apply_result.returncode,
            "stdout": apply_result.stdout or "",
            "stderr": apply_result.stderr or "",
        }

    except Exception as e:
        state_after = {
            "target_files": [_file_state(path_str) for path_str in target_files],
        }
        _write_json(Path(run_dir) / "state_after.json", state_after)

        actual_delta = {
            "apply_rc": 1,
            "patch_hash": patch_hash,
            "target_files": target_files,
            "files_changed": [],
            "exception": str(e),
        }
        _write_json(Path(run_dir) / "actual_delta.json", actual_delta)

        return {
            "ok": False,
            "rc": 1,
            "failure_reason": f"apply_patch_exception:{e}",
            "patch_hash": patch_hash,
            "target_files": target_files,
            "apply_rc": 1,
            "stdout": "",
            "stderr": str(e),
        }
