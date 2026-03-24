"""Minimal CPS Engine - Clean Slate"""
import json, hashlib, subprocess, os, time
from pathlib import Path
from typing import Any, Dict, List

class PolicyEngine:
    ALLOWED_PATHS = ["/Users/axiolevns/axiolev_runtime", "/Volumes/NSExternal", "/app", "/tmp", os.path.expanduser("~")]
    ALLOWED_PROGRAMS = ["git", "docker", "python3", "curl", "ls", "cat"]
    
    @staticmethod
    def is_path_allowed(path: str) -> bool:
        p = Path(path).resolve()
        return any(str(p).startswith(str(Path(ap).resolve())) for ap in PolicyEngine.ALLOWED_PATHS)
    
    @staticmethod
    def is_program_allowed(program: str) -> bool:
        prog_name = program.split()[0]
        return any(prog_name.endswith(allowed) for allowed in PolicyEngine.ALLOWED_PROGRAMS)



def _op_fs_exists(args: Dict[str, Any]) -> Dict[str, Any]:
    path = args.get("path", "")
    try:
        exists = os.path.exists(path)
        return {"ok": True, "data": {"path": path, "exists": exists}, "signal": 0, "latency_ms": 1, "error": None}
    except Exception as e:
        return {"ok": False, "data": None, "signal": -1, "latency_ms": 0, "error": str(e)}

def _op_fs_list(args: Dict[str, Any]) -> Dict[str, Any]:
    path = args.get("path", ".")
    try:
        entries = sorted(os.listdir(path))
        return {"ok": True, "data": {"path": path, "entries": entries}, "signal": 0, "latency_ms": 5, "error": None}
    except Exception as e:
        return {"ok": False, "data": None, "signal": -1, "latency_ms": 0, "error": str(e)}



READONLY_ALLOWLIST = {
    "pwd": ["pwd"],
    "ls": ["ls"],
    "git_status": ["git", "status", "--short", "--branch"],
    "git_log": ["git", "log", "--oneline", "-5"],
}



FS_WRITE_PREFIXES = [
    "/app/handrail/cps/",
]

def _op_fs_write(args: Dict[str, Any]) -> Dict[str, Any]:
    path = args.get("path", "")
    content = args.get("content", "")
    overwrite = bool(args.get("overwrite", False))

    if not any(path.startswith(prefix) for prefix in FS_WRITE_PREFIXES):
        return {
            "ok": False,
            "data": None,
            "signal": -1,
            "latency_ms": 0,
            "error": f"Path not allowed for write: {path}"
        }

    try:
        import os, time
        start = time.time()

        if os.path.exists(path) and not overwrite:
            return {
                "ok": False,
                "data": None,
                "signal": -1,
                "latency_ms": 0,
                "error": f"File exists and overwrite=false: {path}"
            }

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        elapsed = round((time.time() - start) * 1000, 1)
        return {
            "ok": True,
            "data": {
                "path": path,
                "bytes_written": len(content.encode("utf-8"))
            },
            "signal": 0,
            "latency_ms": elapsed,
            "error": None
        }
    except Exception as e:
        return {
            "ok": False,
            "data": None,
            "signal": -1,
            "latency_ms": 0,
            "error": str(e)
        }

def _op_proc_run_readonly(args: Dict[str, Any]) -> Dict[str, Any]:
    import subprocess, time
    command = args.get("command", "")
    cwd = args.get("cwd", "/app")
    if command not in READONLY_ALLOWLIST:
        return {
            "ok": False,
            "data": None,
            "signal": -1,
            "latency_ms": 0,
            "error": f"Command not allowed: {command}"
        }
    try:
        start = time.time()
        cp = subprocess.run(
            READONLY_ALLOWLIST[command],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
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
                "returncode": cp.returncode
            },
            "signal": cp.returncode,
            "latency_ms": elapsed,
            "error": None if cp.returncode == 0 else (cp.stderr or f"returncode={cp.returncode}")
        }
    except Exception as e:
        return {
            "ok": False,
            "data": None,
            "signal": -1,
            "latency_ms": 0,
            "error": str(e)
        }



FS_WRITE_PREFIXES = [
    "/app/handrail/cps/",
    "/Users/axiolevns/axiolev_runtime/services/handrail/handrail/cps/",
]

def _op_fs_write_text(args: Dict[str, Any]) -> Dict[str, Any]:
    import os, time
    path = args.get("path", "")
    content = args.get("content", "")
    overwrite = bool(args.get("overwrite", False))

    if not any(path.startswith(prefix) for prefix in FS_WRITE_PREFIXES):
        return {
            "ok": False,
            "data": None,
            "signal": -1,
            "latency_ms": 0,
            "error": f"path_not_allowed:{path}"
        }

    try:
        start = time.time()
        os.makedirs(os.path.dirname(path), exist_ok=True)

        if os.path.exists(path) and not overwrite:
            return {
                "ok": False,
                "data": None,
                "signal": -1,
                "latency_ms": 0,
                "error": f"exists_overwrite_false:{path}"
            }

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        latency = round((time.time() - start) * 1000, 1)
        return {
            "ok": True,
            "data": {
                "path": path,
                "bytes_written": len(content.encode("utf-8"))
            },
            "signal": 0,
            "latency_ms": latency,
            "error": None
        }
    except Exception as e:
        return {
            "ok": False,
            "data": None,
            "signal": -1,
            "latency_ms": 0,
            "error": str(e)
        }

def _op_fs_read(args: Dict[str, Any]) -> Dict[str, Any]:
    path = args.get("path", "")
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {"ok": True, "data": {"path": path, "content": content}, "signal": 0, "latency_ms": 10, "error": None}
    except Exception as e:
        return {"ok": False, "data": None, "signal": -1, "latency_ms": 0, "error": str(e)}

def _op_http_get(args: Dict[str, Any]) -> Dict[str, Any]:
    import urllib.request, json as json_module
    url = args.get("url", "")
    timeout_ms = args.get("timeout_ms", 3000)
    timeout_s = timeout_ms / 1000
    try:
        response = urllib.request.urlopen(url, timeout=timeout_s)
        body = response.read().decode()
        try:
            body_json = json_module.loads(body)
        except:
            body_json = body
        return {"ok": True, "data": {"status_code": response.status, "body": body_json}, "signal": response.status, "latency_ms": timeout_ms / 10, "error": None}
    except Exception as e:
        return {"ok": False, "data": None, "signal": 0, "latency_ms": 0, "error": str(e)}

def _op_proc_run(args: Dict[str, Any]) -> Dict[str, Any]:
    cmd = args.get("cmd", "")
    timeout_ms = args.get("timeout_ms", 30000)
    timeout_s = timeout_ms / 1000
    if not PolicyEngine.is_program_allowed(cmd):
        return {"ok": False, "data": None, "signal": -1, "latency_ms": 0, "error": f"Program not allowed: {cmd}"}
    try:
        start = time.time()
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout_s)
        elapsed = (time.time() - start) * 1000
        return {"ok": result.returncode == 0, "data": {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}, "signal": result.returncode, "latency_ms": elapsed, "error": None if result.returncode == 0 else result.stderr}
    except subprocess.TimeoutExpired:
        return {"ok": False, "data": None, "signal": -1, "latency_ms": timeout_ms, "error": "Timeout"}
    except Exception as e:
        return {"ok": False, "data": None, "signal": -1, "latency_ms": 0, "error": str(e)}

def _op_fs_pwd(args: Dict[str, Any]) -> Dict[str, Any]:
    try:
        pwd = os.getcwd()
        return {"ok": True, "data": {"path": pwd}, "signal": 0, "latency_ms": 1, "error": None}
    except Exception as e:
        return {"ok": False, "data": None, "signal": -1, "latency_ms": 0, "error": str(e)}

def _op_fs_list(args: Dict[str, Any]) -> Dict[str, Any]:
    path = args.get("path", ".")
    if not PolicyEngine.is_path_allowed(path):
        return {"ok": False, "data": None, "signal": -1, "latency_ms": 0, "error": f"Path not allowed: {path}"}
    try:
        entries = sorted(os.listdir(path))
        return {"ok": True, "data": {"entries": entries}, "signal": 0, "latency_ms": 5, "error": None}
    except Exception as e:
        return {"ok": False, "data": None, "signal": -1, "latency_ms": 0, "error": str(e)}



READONLY_ALLOWLIST = {
    "pwd": ["pwd"],
    "ls": ["ls"],
    "git_status": ["git", "status", "--short", "--branch"],
    "git_log": ["git", "log", "--oneline", "-5"],
}



FS_WRITE_PREFIXES = [
    "/app/handrail/cps/",
]

def _op_fs_write(args: Dict[str, Any]) -> Dict[str, Any]:
    path = args.get("path", "")
    content = args.get("content", "")
    overwrite = bool(args.get("overwrite", False))

    if not any(path.startswith(prefix) for prefix in FS_WRITE_PREFIXES):
        return {
            "ok": False,
            "data": None,
            "signal": -1,
            "latency_ms": 0,
            "error": f"Path not allowed for write: {path}"
        }

    try:
        import os, time
        start = time.time()

        if os.path.exists(path) and not overwrite:
            return {
                "ok": False,
                "data": None,
                "signal": -1,
                "latency_ms": 0,
                "error": f"File exists and overwrite=false: {path}"
            }

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        elapsed = round((time.time() - start) * 1000, 1)
        return {
            "ok": True,
            "data": {
                "path": path,
                "bytes_written": len(content.encode("utf-8"))
            },
            "signal": 0,
            "latency_ms": elapsed,
            "error": None
        }
    except Exception as e:
        return {
            "ok": False,
            "data": None,
            "signal": -1,
            "latency_ms": 0,
            "error": str(e)
        }

def _op_proc_run_readonly(args: Dict[str, Any]) -> Dict[str, Any]:
    import subprocess, time
    command = args.get("command", "")
    cwd = args.get("cwd", "/app")
    if command not in READONLY_ALLOWLIST:
        return {
            "ok": False,
            "data": None,
            "signal": -1,
            "latency_ms": 0,
            "error": f"Command not allowed: {command}"
        }
    try:
        start = time.time()
        cp = subprocess.run(
            READONLY_ALLOWLIST[command],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
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
                "returncode": cp.returncode
            },
            "signal": cp.returncode,
            "latency_ms": elapsed,
            "error": None if cp.returncode == 0 else (cp.stderr or f"returncode={cp.returncode}")
        }
    except Exception as e:
        return {
            "ok": False,
            "data": None,
            "signal": -1,
            "latency_ms": 0,
            "error": str(e)
        }



FS_WRITE_PREFIXES = [
    "/app/handrail/cps/",
    "/Users/axiolevns/axiolev_runtime/services/handrail/handrail/cps/",
]

def _op_fs_write_text(args: Dict[str, Any]) -> Dict[str, Any]:
    import os, time
    path = args.get("path", "")
    content = args.get("content", "")
    overwrite = bool(args.get("overwrite", False))

    if not any(path.startswith(prefix) for prefix in FS_WRITE_PREFIXES):
        return {
            "ok": False,
            "data": None,
            "signal": -1,
            "latency_ms": 0,
            "error": f"path_not_allowed:{path}"
        }

    try:
        start = time.time()
        os.makedirs(os.path.dirname(path), exist_ok=True)

        if os.path.exists(path) and not overwrite:
            return {
                "ok": False,
                "data": None,
                "signal": -1,
                "latency_ms": 0,
                "error": f"exists_overwrite_false:{path}"
            }

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        latency = round((time.time() - start) * 1000, 1)
        return {
            "ok": True,
            "data": {
                "path": path,
                "bytes_written": len(content.encode("utf-8"))
            },
            "signal": 0,
            "latency_ms": latency,
            "error": None
        }
    except Exception as e:
        return {
            "ok": False,
            "data": None,
            "signal": -1,
            "latency_ms": 0,
            "error": str(e)
        }

def _op_fs_read(args: Dict[str, Any]) -> Dict[str, Any]:
    path = args.get("path", "")
    if not PolicyEngine.is_path_allowed(path):
        return {"ok": False, "data": None, "signal": -1, "latency_ms": 0, "error": f"Path not allowed: {path}"}
    try:
        with open(path, "r") as f:
            content = f.read()
        return {"ok": True, "data": {"content": content}, "signal": 0, "latency_ms": 10, "error": None}
    except Exception as e:
        return {"ok": False, "data": None, "signal": -1, "latency_ms": 0, "error": str(e)}

def _op_git_status(args: Dict[str, Any]) -> Dict[str, Any]:
    repo = args.get("repo", ".")
    if not PolicyEngine.is_path_allowed(repo):
        return {"ok": False, "data": None, "signal": -1, "latency_ms": 0, "error": f"Path not allowed: {repo}"}
    try:
        result = subprocess.run(f"cd {repo} && git status --porcelain", shell=True, capture_output=True, text=True, timeout=5)
        return {"ok": result.returncode == 0, "data": {"status": result.stdout}, "signal": result.returncode, "latency_ms": 20, "error": None if result.returncode == 0 else result.stderr}
    except Exception as e:
        return {"ok": False, "data": None, "signal": -1, "latency_ms": 0, "error": str(e)}

def _op_git_log(args: Dict[str, Any]) -> Dict[str, Any]:
    repo = args.get("repo", ".")
    if not PolicyEngine.is_path_allowed(repo):
        return {"ok": False, "data": None, "signal": -1, "latency_ms": 0, "error": f"Path not allowed: {repo}"}
    try:
        result = subprocess.run(f"cd {repo} && git log --oneline -5", shell=True, capture_output=True, text=True, timeout=5)
        return {"ok": result.returncode == 0, "data": {"log": result.stdout}, "signal": result.returncode, "latency_ms": 20, "error": None if result.returncode == 0 else result.stderr}
    except Exception as e:
        return {"ok": False, "data": None, "signal": -1, "latency_ms": 0, "error": str(e)}

OP_DISPATCH = {
    "http.get": _op_http_get,
    "fs.exists": _op_fs_exists,
    "fs.list": _op_fs_list,
    "fs.read": _op_fs_read,
    "fs.write_text": _op_fs_write_text,
    "proc.run_readonly": _op_proc_run_readonly,
    "fs.write": _op_fs_write,
    "proc.run": _op_proc_run,
    "fs.pwd": _op_fs_pwd,
    "fs.list": _op_fs_list,
    "fs.read": _op_fs_read,
    "fs.write_text": _op_fs_write_text,
    "proc.run_readonly": _op_proc_run_readonly,
    "fs.write": _op_fs_write,
    "git.status": _op_git_status,
    "git.log": _op_git_log,
}

class CPSExecutor:
    @staticmethod
    def execute(cps_dict: Dict[str, Any], workspace: str = None) -> Dict[str, Any]:
        cps_id = cps_dict.get("cps_id", "unknown")
        objective = cps_dict.get("objective", "")
        ops = cps_dict.get("ops", [])
        expect = cps_dict.get("expect", {})
        results = []
        ok_overall = True
        
        for idx, op in enumerate(ops):
            op_type = op.get("op", "")
            op_args = op.get("args", {})
            
            if op_type not in OP_DISPATCH:
                result = {"op_index": idx, "op": op_type, "ok": False, "data": None, "signal": -1, "latency_ms": 0, "error": f"Unknown operation: {op_type}", "decision_code": "OP_NOT_FOUND"}
                ok_overall = False
            else:
                try:
                    handler_result = OP_DISPATCH[op_type](op_args)
                    result = {"op_index": idx, "op": op_type, "ok": handler_result.get("ok", False), "data": handler_result.get("data"), "signal": handler_result.get("signal", 0), "latency_ms": handler_result.get("latency_ms", 0), "error": handler_result.get("error"), "decision_code": "OK" if handler_result.get("ok") else "FAILED"}
                    if not handler_result.get("ok"):
                        ok_overall = False
                except Exception as e:
                    result = {"op_index": idx, "op": op_type, "ok": False, "data": None, "signal": -1, "latency_ms": 0, "error": str(e), "decision_code": "EXCEPTION"}
                    ok_overall = False
            
            results.append(result)
        
        result_digest = hashlib.sha256(json.dumps(results, sort_keys=True, default=str).encode()).hexdigest()
        
        response = {
            "cps_id": cps_id,
            "objective": objective,
            "ok": ok_overall,
            "results": results,
            "result_digest": f"sha256:{result_digest}",
            "metrics": {"op_count": len(ops), "duration_ms": sum(r.get("latency_ms", 0) for r in results)}
        }
        
        return response
