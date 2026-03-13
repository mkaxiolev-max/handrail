from __future__ import annotations

import hashlib
import shlex
import shutil
import subprocess
from pathlib import Path

ALLOWED_ROOT = Path("/app")
ALLOWED_TEST_BINARIES = {"pytest", "python3", "python"}
BLOCKED_TOKENS = {";", "&&", "||", ">", ">>", "<", "|", "$(", "`"}

def _validate_test_command(raw_cmd: str) -> tuple[bool, str | None, list[str] | None]:
    raw_cmd = (raw_cmd or "").strip()
    if not raw_cmd:
        raw_cmd = "python3 -m pytest -q"

    for token in BLOCKED_TOKENS:
        if token in raw_cmd:
            return False, f"blocked_token:{token}", None

    try:
        argv = shlex.split(raw_cmd)
    except Exception:
        return False, "invalid_shell_syntax", None

    if not argv:
        return False, "empty_argv", None

    binary = argv[0]
    if binary not in ALLOWED_TEST_BINARIES:
        return False, f"unsupported_test_binary:{binary}", None

    if binary in {"python", "python3"}:
        if len(argv) < 3 or argv[1] != "-m" or argv[2] != "pytest":
            return False, "python_only_allows_module_pytest", None

    return True, None, argv

def _binary_available(argv: list[str]) -> tuple[bool, str | None]:
    if not argv:
        return False, "empty_argv"

    binary = argv[0]

    if binary == "pytest":
        return (shutil.which("pytest") is not None, "missing_binary:pytest")

    if binary in {"python", "python3"}:
        found = shutil.which(binary)
        if not found:
            return False, f"missing_binary:{binary}"
        return True, None

    return False, f"unsupported_test_binary:{binary}"

def run_tests(task_request: dict, run_dir: Path) -> dict:
    raw_cmd = task_request.get("test_command", "python3 -m pytest -q")
    ok, reason, argv = _validate_test_command(raw_cmd)

    if not ok:
        return {
            "ok": False,
            "rc": 400,
            "failure_reason": reason,
            "command": raw_cmd,
            "argv": argv,
            "stdout": "",
            "stderr": reason or "",
            "test_command": raw_cmd,
        }

    available, availability_reason = _binary_available(argv)
    if not available:
        return {
            "ok": False,
            "rc": 400,
            "failure_reason": availability_reason,
            "command": raw_cmd,
            "argv": argv,
            "stdout": "",
            "stderr": availability_reason or "",
            "test_command": raw_cmd,
        }

    command_hash = hashlib.sha256(raw_cmd.encode("utf-8")).hexdigest()

    try:
        result = subprocess.run(
            argv,
            cwd=ALLOWED_ROOT,
            capture_output=True,
            text=True,
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""

        (Path(run_dir) / "tests_stdout.txt").write_text(stdout, encoding="utf-8")
        (Path(run_dir) / "tests_stderr.txt").write_text(stderr, encoding="utf-8")

        return {
            "ok": result.returncode == 0,
            "rc": result.returncode,
            "failure_reason": None if result.returncode == 0 else "tests_failed",
            "command": raw_cmd,
            "argv": argv,
            "command_hash": command_hash,
            "stdout": stdout,
            "stderr": stderr,
            "test_command": raw_cmd,
        }

    except Exception as e:
        return {
            "ok": False,
            "rc": 1,
            "failure_reason": f"run_tests_exception:{e}",
            "command": raw_cmd,
            "argv": argv,
            "command_hash": command_hash,
            "stdout": "",
            "stderr": str(e),
            "test_command": raw_cmd,
        }
