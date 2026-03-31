"""
Handrail CPS Engine — Phase 1
Normalized result shape, external policy profiles, expect validation,
metrics, artifact manifest, docker.compose_up support.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------

POLICY_DIR = Path(__file__).parent / "policy"

BUILTIN_POLICIES: dict[str, dict] = {
    "readonly.local": {
        "name": "readonly.local",
        "allowed_paths": ["/Volumes/NSExternal", "/workspace", "/tmp", "/var/tmp"],
        "allowed_programs": ["pwd", "ls", "cat", "tail", "head", "wc", "find", "git", "curl"],
        "allow_mutation": False,
    },
    "repo.inspect": {
        "name": "repo.inspect",
        "allowed_paths": ["/workspace", "/Volumes/NSExternal", "/tmp"],
        "allowed_programs": ["git", "pwd", "ls", "cat", "curl"],
        "allow_mutation": False,
    },
    "boot.runtime": {
        "name": "boot.runtime",
        "allowed_paths": ["/workspace", "/Volumes/NSExternal", "/tmp", "/var/tmp"],
        "allowed_programs": ["docker", "curl", "python3", "bash", "sh", "git", "pwd", "ls", "cat"],
        "allow_mutation": True,
    },
    "default": {
        "name": "default",
        "allowed_paths": ["/workspace", "/tmp"],
        "allowed_programs": ["pwd", "ls", "cat", "git", "curl"],
        "allow_mutation": False,
    },
}


def load_policy(profile_name: str | None) -> dict:
    name = profile_name or "default"
    # Try external file first
    external = POLICY_DIR / f"{name}.json"
    if external.exists():
        return json.loads(external.read_text())
    # Fall back to builtin
    if name in BUILTIN_POLICIES:
        return BUILTIN_POLICIES[name]
    raise ValueError(f"Unknown policy profile: {name!r}")


class PolicyEngine:
    def __init__(self, profile: dict):
        self.profile = profile

    def check_path(self, path: str) -> bool:
        return any(path.startswith(p) for p in self.profile.get("allowed_paths", []))

    def check_program(self, program: str) -> bool:
        return program in self.profile.get("allowed_programs", [])

    def allow_mutation(self) -> bool:
        return bool(self.profile.get("allow_mutation", False))


# ---------------------------------------------------------------------------
# Digest helpers
# ---------------------------------------------------------------------------

def _sha256(data: Any) -> str:
    raw = json.dumps(data, sort_keys=True, default=str).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return "sha256:" + h.hexdigest()


# ---------------------------------------------------------------------------
# Op handlers
# ---------------------------------------------------------------------------

def _op_fs_pwd(_args: dict, _policy: PolicyEngine) -> dict:
    import os
    return {"cwd": os.getcwd()}


def _op_fs_list(args: dict, policy: PolicyEngine) -> dict:
    path = args.get("path", ".")
    if not policy.check_path(str(Path(path).resolve())):
        raise PermissionError(f"Path not allowed: {path}")
    entries = sorted(Path(path).iterdir(), key=lambda p: p.name)
    return {"entries": [{"name": e.name, "type": "dir" if e.is_dir() else "file"} for e in entries]}


def _op_fs_read(args: dict, policy: PolicyEngine) -> dict:
    path = args.get("path", "")
    if not policy.check_path(str(Path(path).resolve())):
        raise PermissionError(f"Path not allowed: {path}")
    content = Path(path).read_text()
    return {"content": content, "size": len(content)}


def _op_git_status(args: dict, _policy: PolicyEngine) -> dict:
    repo = args.get("repo", "/workspace")
    result = subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True, text=True, timeout=10)
    return {"output": result.stdout, "clean": result.stdout.strip() == "", "returncode": result.returncode}


def _op_git_log(args: dict, _policy: PolicyEngine) -> dict:
    repo = args.get("repo", "/workspace")
    limit = args.get("limit", 5)
    oneline = args.get("oneline", True)
    fmt = "--oneline" if oneline else "--format=%H %s"
    result = subprocess.run(["git", "-C", repo, "log", fmt, f"-{limit}"], capture_output=True, text=True, timeout=10)
    return {"output": result.stdout.strip(), "returncode": result.returncode}


def _op_docker_compose_ps(args: dict, policy: PolicyEngine) -> dict:
    if not policy.check_program("docker"):
        raise PermissionError("docker not in allowed programs")
    project_dir = args.get("project_dir", "/workspace")
    result = subprocess.run(
        ["docker", "compose", "-f", f"{project_dir}/docker-compose.yml", "ps", "--format", "json"],
        capture_output=True, text=True, timeout=15,
    )
    try:
        services = json.loads(result.stdout) if result.stdout.strip() else []
    except json.JSONDecodeError:
        services = result.stdout.strip()
    return {"services": services, "returncode": result.returncode}


def _op_docker_compose_up(args: dict, policy: PolicyEngine) -> dict:
    if not policy.check_program("docker"):
        raise PermissionError("docker not in allowed programs")
    if not policy.allow_mutation():
        raise PermissionError("Policy does not allow mutation (compose up)")
    project_dir = args.get("project_dir", "/workspace")
    detached = args.get("detached", True)
    build = args.get("build", False)
    cmd = ["docker", "compose", "-f", f"{project_dir}/docker-compose.yml", "up"]
    if detached:
        cmd.append("-d")
    if build:
        cmd.append("--build")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return {"returncode": result.returncode, "stdout": result.stdout[-500:], "stderr": result.stderr[-500:]}


def _op_http_get(args: dict, _policy: PolicyEngine) -> dict:
    url = args.get("url", "")
    timeout_ms = args.get("timeout_ms", 5000)
    try:
        resp = httpx.get(url, timeout=timeout_ms / 1000)
        try:
            body = resp.json()
        except Exception:
            body = resp.text[:500]
        return {"status_code": resp.status_code, "body": body}
    except httpx.TimeoutException:
        raise TimeoutError(f"GET {url} timed out after {timeout_ms}ms")
    except Exception as e:
        raise RuntimeError(f"GET {url} failed: {e}")


def _op_proc_run_readonly(args: dict, policy: PolicyEngine) -> dict:
    # Accepts either cmd (list) or command (str)
    cmd = args.get("cmd") or args.get("command")
    if not cmd:
        raise ValueError("proc.run_readonly requires cmd list or command string")
    if isinstance(cmd, str):
        cmd = cmd.split()
    program = cmd[0].split("/")[-1]
    if not policy.check_program(program):
        raise PermissionError(f"Program not allowed: {program}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def _op_proc_run(args: dict, policy: PolicyEngine) -> dict:
    cmd = args.get("cmd", [])
    if not cmd:
        raise ValueError("proc.run_allowed requires cmd list")
    program = cmd[0].split("/")[-1]
    if not policy.check_program(program):
        raise PermissionError(f"Program not allowed: {program}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


OP_DISPATCH: dict[str, Any] = {
    "fs.pwd": _op_fs_pwd,
    "fs.list": _op_fs_list,
    "fs.read": _op_fs_read,
    "git.status": _op_git_status,
    "git.log": _op_git_log,
    "proc.run_readonly": _op_proc_run_readonly,
    "docker.compose_ps": _op_docker_compose_ps,
    "docker.compose_up": _op_docker_compose_up,
    "http.get": _op_http_get,
    "proc.run_allowed": _op_proc_run,
}


# ---------------------------------------------------------------------------
# Expect validation
# ---------------------------------------------------------------------------

def _resolve_path(obj: Any, path: str) -> Any:
    """Resolve dot-bracket path like results[1].data.status_code"""
    import re
    parts = re.split(r"\.|\[(\d+)\]", path)
    cur = obj
    for part in parts:
        if part is None or part == "":
            continue
        if isinstance(cur, list):
            cur = cur[int(part)]
        elif isinstance(cur, dict):
            cur = cur[part]
        else:
            raise KeyError(f"Cannot traverse into {type(cur)} at {part!r}")
    return cur


def _validate_expect(results: list, expect: dict) -> dict:
    failures = []
    for path, expected in expect.items():
        try:
            actual = _resolve_path({"results": results}, path)
            if actual != expected:
                failures.append({"path": path, "expected": expected, "actual": actual})
        except Exception as e:
            failures.append({"path": path, "expected": expected, "actual": f"ERROR: {e}"})
    return {"passed": len(failures) == 0, "failures": failures}


# ---------------------------------------------------------------------------
# Main executor
# ---------------------------------------------------------------------------

OP_DISPATCH = {
    "fs.pwd": _op_fs_pwd,
    "fs.list": _op_fs_list,
    "fs.read": _op_fs_read,
    "git.status": _op_git_status,
    "git.log": _op_git_log,
    "docker.compose_ps": _op_docker_compose_ps,
    "docker.compose_up": _op_docker_compose_up,
    "http.get": _op_http_get,
    "proc.run": _op_proc_run,
}


READONLY_ALLOWLIST = {
    "pwd": ["pwd"],
    "ls": ["ls"],
    "git_status": ["git", "status", "--short", "--branch"],
    "git_log": ["git", "log", "--oneline", "-5"],
    "pytest_smoke": ["pytest", "-q", "tests"],
    "docker_ps": ["docker", "ps", "--format", "{{.Names}}|{{.Status}}|{{.Ports}}"],
    "recent_handrail_logs": ["sh", "-lc", "ls -1dt /app/handrail/.run/* 2>/dev/null | head -n 1 | xargs -I{} sh -lc 'find \"{}\" -maxdepth 2 -type f | sort | tail -n 20'"],
}

def _op_proc_run_readonly(args):
    import subprocess, time, os

    command = args.get("command")
    cwd = args.get("cwd", "/app")

    allowed = {
        "pwd": ["pwd"],
        "ls": ["ls"],
    }

    if command not in allowed:
        return {
            "ok": False,
            "data": {},
            "signal": None,
            "error": f"not allowed: {command}",
            "latency_ms": 0.0,
        }

    try:
        start = time.time()
        cp = subprocess.run(
            allowed[command],
            cwd=cwd,
            capture_output=True,
            text=True
        )

        elapsed = int((time.time() - start) * 1000)

        return {
            "ok": cp.returncode == 0,
            "data": {
                "stdout": cp.stdout,
                "stderr": cp.stderr,
                "returncode": cp.returncode,
                "command": command,
                "cwd": cwd,
            },
            "signal": cp.returncode,
            "error": None if cp.returncode == 0 else (cp.stderr or "nonzero exit"),
            "latency_ms": elapsed,
        }

    except Exception as e:
        return {
            "ok": False,
            "data": {
                "command": command,
                "cwd": cwd,
            },
            "signal": None,
            "error": str(e),
            "latency_ms": 0,
        }

    if not os.path.isdir(cwd):
        return {
            "ok": False,
            "data": {},
            "signal": None,
            "error": f"Invalid cwd: {cwd}",
            "latency_ms": 0.0,
        }

    try:
        start = time.time()
        cp = subprocess.run(
            READONLY_ALLOWLIST[command],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        elapsed = round((time.time() - start) * 1000, 1)
        return {
            "ok": cp.returncode == 0,
            "data": {
                "command": command,
                "cwd": cwd,
                "stdout": cp.stdout,
                "stderr": cp.stderr,
                "returncode": cp.returncode,
            },
            "signal": cp.returncode,
            "error": None if cp.returncode == 0 else (cp.stderr or f"returncode={cp.returncode}"),
            "latency_ms": elapsed,
        }
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False,
            "data": {
                "command": command,
                "cwd": cwd,
                "stdout": e.stdout,
                "stderr": e.stderr,
                "returncode": None,
            },
            "signal": None,
            "error": f"timeout: {command}",
            "latency_ms": 30000.0,
        }
    except Exception as e:
        return {
            "ok": False,
            "data": {
                "command": command,
                "cwd": cwd,
            },
            "signal": None,
            "error": f"{type(e).__name__}: {e}",
            "latency_ms": 0.0,
        }


class CPSExecutor:
    @staticmethod
    def execute(cps: dict, workspace: Path | None = None) -> dict:
        policy_profile_name = cps.get("policy_profile")
        policy_data = load_policy(policy_profile_name)
        policy = PolicyEngine(policy_data)

        ops = cps.get("ops", [])
        expect = cps.get("expect", {})

        results: list[dict] = []
        all_ok = True
        start_total = time.monotonic()

        for idx, op_spec in enumerate(ops):
            op_name = op_spec.get("op", "")
            op_args = op_spec.get("args", {})
            start_op = time.monotonic()
            result: dict = {
                "op_index": idx,
                "op": op_name,
                "args": op_args,
                "ok": False,
                "data": {},
                "signal": None,
                "error": None,
                "latency_ms": 0,
                "decision_code": "PENDING",
                "op_digest": "",
            }

            handler = OP_DISPATCH.get(op_name)
            if handler is None:
                result["error"] = f"Unknown op: {op_name}"
                result["decision_code"] = "UNKNOWN_OP"
                all_ok = False
            else:
                try:
                    data = handler(op_args, policy)
                    result["ok"] = True
                    result["data"] = data
                    result["decision_code"] = "OK"
                    # Derive signal
                    if "status_code" in data:
                        result["signal"] = data["status_code"]
                    elif "returncode" in data:
                        result["signal"] = data["returncode"]
                    else:
                        result["signal"] = "ok"
                except PermissionError as e:
                    result["error"] = str(e)
                    result["decision_code"] = "POLICY_DENIED"
                    all_ok = False
                except TimeoutError as e:
                    result["error"] = str(e)
                    result["decision_code"] = "TIMEOUT"
                    all_ok = False
                except Exception as e:
                    result["error"] = str(e)
                    result["decision_code"] = "OP_ERROR"
                    all_ok = False

            result["latency_ms"] = round((time.monotonic() - start_op) * 1000, 1)
            result["op_digest"] = _sha256({"op": op_name, "args": op_args, "data": result["data"]})
            results.append(result)

        duration_ms = round((time.monotonic() - start_total) * 1000, 1)
        expect_result = _validate_expect(results, expect) if expect else {"passed": True, "failures": []}
        result_digest = _sha256(results)

        return {
            "cps_id": cps.get("cps_id"),
            "ok": all_ok and expect_result["passed"],
            "results": results,
            "expect_result": expect_result,
            "metrics": {
                "op_count": len(ops),
                "typed_ops_ratio": 1.0,
                "duration_ms": duration_ms,
            },
            "result_digest": result_digest,
            "policy_profile": policy_profile_name or "default",
        }

    @staticmethod
    def handle_app_focus(args):
        import subprocess
        app_name = args.get("app_name")
        try:
            subprocess.run(["osascript", "-e", f'tell application "{app_name}" to activate'], timeout=5, check=True, capture_output=True)
            return {"ok": True, "focused": True}
        except:
            return {"ok": False, "error": "focus_failed"}

    @staticmethod
    def handle_ui_click(args):
        x, y = args.get("x", 0), args.get("y", 0)
        import subprocess
        try:
            subprocess.run(["osascript", "-e", f'tell application "System Events" to click at {{{x}, {y}}}'], timeout=5, check=True, capture_output=True)
            return {"ok": True, "clicked": True}
        except:
            return {"ok": False, "error": "click_failed"}

    @staticmethod
    def handle_ui_type(args):
        text = args.get("text", "").replace('"', '\\"')
        import subprocess
        try:
            subprocess.run(["osascript", "-e", f'tell application "System Events" to keystroke "{text}"'], timeout=5, check=True, capture_output=True)
            return {"ok": True, "typed": True}
        except:
            return {"ok": False, "error": "type_failed"}

    @staticmethod
    def handle_vision_capture(args):
        import subprocess, time
        artifact_path = f"/Volumes/NSExternal/.run/boot/screen_{int(time.time()*1000)}.png"
        try:
            subprocess.run(["screencapture", "-x", artifact_path], timeout=5, check=True)
            return {"ok": True, "captured": True, "artifact": artifact_path}
        except:
            return {"ok": False, "error": "capture_failed"}

    @staticmethod
    def handle_fs_read(args):
        path = args.get("path")
        try:
            with open(path, 'r') as f:
                content = f.read()
            return {"ok": True, "read": True, "content": content, "length": len(content)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

def _op_app_focus(args: dict, _policy: PolicyEngine) -> dict:
    import subprocess
    app_name = args.get("app_name")
    try:
        subprocess.run(["osascript", "-e", f'tell application "{app_name}" to activate'], timeout=5, check=True, capture_output=True)
        return {"ok": True, "focused": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _op_ui_click(args: dict, _policy: PolicyEngine) -> dict:
    import subprocess
    x, y = args.get("x", 0), args.get("y", 0)
    try:
        subprocess.run(["osascript", "-e", f'tell application "System Events" to click at {{{x}, {y}}}'], timeout=5, check=True, capture_output=True)
        return {"ok": True, "clicked": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _op_ui_type(args: dict, _policy: PolicyEngine) -> dict:
    import subprocess
    text = args.get("text", "").replace('"', '\\"')
    try:
        subprocess.run(["osascript", "-e", f'tell application "System Events" to keystroke "{text}"'], timeout=5, check=True, capture_output=True)
        return {"ok": True, "typed": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _op_vision_capture(args: dict, _policy: PolicyEngine) -> dict:
    import subprocess, time
    artifact_path = f"/Volumes/NSExternal/.run/boot/screen_{int(time.time()*1000)}.png"
    try:
        subprocess.run(["screencapture", "-x", artifact_path], timeout=5, check=True)
        return {"ok": True, "captured": True, "artifact": artifact_path}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _op_fs_read_full(args: dict, _policy: PolicyEngine) -> dict:
    path = args.get("path")
    try:
        with open(path, 'r') as f:
            content = f.read()
        return {"ok": True, "read": True, "content": content, "length": len(content)}
    except Exception as e:
        return {"ok": False, "error": str(e)}
