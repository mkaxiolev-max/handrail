"""
CPS Engine: Deterministic transaction executor for Handrail
Converts structured operation arrays into typed, policy-enforced execution.
"""

from __future__ import annotations
import json
import hashlib
import subprocess
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class OpResult:
    """Single operation result"""
    op_index: int
    op_type: str
    ok: bool
    data: Dict[str, Any] = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    decision_code: str = "OK"


class PolicyEngine:
    """Minimal policy enforcement: paths, programs, reason codes"""
    
    ALLOWED_PATHS = {
        "/Volumes/NSExternal",
        "/workspace",
        "/tmp",
        "/var/tmp",
    }
    
    ALLOWED_PROGRAMS = {
        "pwd", "ls", "cat", "tail", "head", "wc", "find",
        "git", "docker", "curl", "python3", "bash", "sh"
    }
    
    DECISION_CODES = {
        "ALLOW_PATH": "path whitelisted",
        "DENY_PATH": "path blocked",
        "ALLOW_PROGRAM": "program whitelisted",
        "DENY_PROGRAM": "program not allowed",
        "EXPECT_PASS": "expect condition satisfied",
        "EXPECT_FAIL": "expect condition failed",
        "TIMEOUT": "operation timed out",
        "INVALID_OP": "operation type unknown",
    }
    
    @staticmethod
    def is_path_allowed(path: str) -> tuple[bool, str]:
        """Check if path is whitelisted"""
        p = Path(path).resolve()
        for allowed in PolicyEngine.ALLOWED_PATHS:
            try:
                p.relative_to(allowed)
                return True, "ALLOW_PATH"
            except ValueError:
                pass
        return False, "DENY_PATH"
    
    @staticmethod
    def is_program_allowed(program: str) -> tuple[bool, str]:
        """Check if program is whitelisted"""
        prog = Path(program).name if "/" in program else program
        if prog in PolicyEngine.ALLOWED_PROGRAMS:
            return True, "ALLOW_PROGRAM"
        return False, "DENY_PROGRAM"


class TypedActionDispatcher:
    """Routes typed operations to handlers"""
    
    @staticmethod
    def dispatch(op: Dict[str, Any], workspace: Path) -> OpResult:
        """Dispatch single typed operation"""
        op_type = op.get("op", "unknown")
        op_index = op.get("_index", 0)
        args = op.get("args", {})
        
        t0 = time.time()
        
        try:
            if op_type == "fs.pwd":
                result = TypedActionDispatcher._fs_pwd(workspace)
            elif op_type == "fs.list":
                result = TypedActionDispatcher._fs_list(workspace, args)
            elif op_type == "fs.read_text":
                result = TypedActionDispatcher._fs_read_text(workspace, args)
            elif op_type == "fs.mkdir":
                result = TypedActionDispatcher._fs_mkdir(workspace, args)
            elif op_type == "git.status":
                result = TypedActionDispatcher._git_status(workspace, args)
            elif op_type == "git.log":
                result = TypedActionDispatcher._git_log(workspace, args)
            elif op_type == "docker.compose_ps":
                result = TypedActionDispatcher._docker_compose_ps(workspace, args)
            elif op_type == "http.get":
                result = TypedActionDispatcher._http_get(args)
            elif op_type == "proc.run_allowed":
                result = TypedActionDispatcher._proc_run_allowed(workspace, args)
            else:
                return OpResult(op_index, op_type, False, error=f"unknown_op:{op_type}", 
                               decision_code="INVALID_OP", latency_ms=(time.time()-t0)*1000)
            
            latency = (time.time() - t0) * 1000
            return OpResult(op_index, op_type, result.get("ok", False), 
                           data=result.get("data"), error=result.get("error"),
                           latency_ms=latency, decision_code=result.get("decision_code", "OK"))
        
        except Exception as e:
            return OpResult(op_index, op_type, False, error=str(e),
                           latency_ms=(time.time()-t0)*1000)
    
    @staticmethod
    def _fs_pwd(workspace: Path) -> Dict:
        return {"ok": True, "data": {"cwd": str(workspace)}, "decision_code": "ALLOW_PATH"}
    
    @staticmethod
    def _fs_list(workspace: Path, args: Dict) -> Dict:
        path = Path(args.get("path", workspace))
        allowed, code = PolicyEngine.is_path_allowed(str(path))
        if not allowed:
            return {"ok": False, "error": f"path_blocked:{path}", "decision_code": code}
        try:
            entries = [e.name for e in path.iterdir()]
            return {"ok": True, "data": {"path": str(path), "entries": sorted(entries)}, "decision_code": code}
        except Exception as e:
            return {"ok": False, "error": str(e), "decision_code": code}
    
    @staticmethod
    def _fs_read_text(workspace: Path, args: Dict) -> Dict:
        path = Path(args.get("path", workspace / "README.md"))
        allowed, code = PolicyEngine.is_path_allowed(str(path))
        if not allowed:
            return {"ok": False, "error": f"path_blocked:{path}", "decision_code": code}
        try:
            content = path.read_text()
            return {"ok": True, "data": {"path": str(path), "size": len(content)}, "decision_code": code}
        except Exception as e:
            return {"ok": False, "error": str(e), "decision_code": code}
    
    @staticmethod
    def _fs_mkdir(workspace: Path, args: Dict) -> Dict:
        path = Path(args.get("path", workspace / "tmp"))
        allowed, code = PolicyEngine.is_path_allowed(str(path))
        if not allowed:
            return {"ok": False, "error": f"path_blocked:{path}", "decision_code": code}
        try:
            path.mkdir(parents=True, exist_ok=True)
            return {"ok": True, "data": {"path": str(path)}, "decision_code": code}
        except Exception as e:
            return {"ok": False, "error": str(e), "decision_code": code}
    
    @staticmethod
    def _git_status(workspace: Path, args: Dict) -> Dict:
        repo = Path(args.get("repo", workspace))
        allowed, code = PolicyEngine.is_path_allowed(str(repo))
        if not allowed:
            return {"ok": False, "error": f"path_blocked:{repo}", "decision_code": code}
        try:
            p = subprocess.run(["git", "status", "--porcelain"], cwd=str(repo),
                             capture_output=True, text=True, timeout=5)
            return {"ok": p.returncode == 0, "data": {"status": p.stdout}, "decision_code": code}
        except Exception as e:
            return {"ok": False, "error": str(e), "decision_code": code}
    
    @staticmethod
    def _git_log(workspace: Path, args: Dict) -> Dict:
        repo = Path(args.get("repo", workspace))
        allowed, code = PolicyEngine.is_path_allowed(str(repo))
        if not allowed:
            return {"ok": False, "error": f"path_blocked:{repo}", "decision_code": code}
        try:
            p = subprocess.run(["git", "log", "--oneline", "-5"], cwd=str(repo),
                             capture_output=True, text=True, timeout=5)
            return {"ok": p.returncode == 0, "data": {"log": p.stdout}, "decision_code": code}
        except Exception as e:
            return {"ok": False, "error": str(e), "decision_code": code}
    
    @staticmethod
    def _docker_compose_ps(workspace: Path, args: Dict) -> Dict:
        compose_file = Path(args.get("compose_file", workspace / "docker-compose.yml"))
        allowed, code = PolicyEngine.is_path_allowed(str(compose_file))
        if not allowed:
            return {"ok": False, "error": f"path_blocked:{compose_file}", "decision_code": code}
        try:
            p = subprocess.run(["docker-compose", "-f", str(compose_file), "ps"],
                             cwd=str(workspace), capture_output=True, text=True, timeout=10)
            return {"ok": p.returncode == 0, "data": {"ps": p.stdout}, "decision_code": code}
        except Exception as e:
            return {"ok": False, "error": str(e), "decision_code": code}
    
    @staticmethod
    def _http_get(args: Dict) -> Dict:
        url = args.get("url", "")
        if not url:
            return {"ok": False, "error": "missing_url"}
        try:
            import urllib.request
            with urllib.request.urlopen(url, timeout=5) as r:
                status = r.status
                return {"ok": 200 <= status < 300, "data": {"status": status}, "decision_code": "OK"}
        except Exception as e:
            return {"ok": False, "error": str(e), "decision_code": "OK"}
    
    @staticmethod
    def _proc_run_allowed(workspace: Path, args: Dict) -> Dict:
        cmd = args.get("cmd", "")
        prog = Path(cmd.split()[0]).name if cmd else ""
        allowed, code = PolicyEngine.is_program_allowed(prog)
        if not allowed:
            return {"ok": False, "error": f"program_not_allowed:{prog}", "decision_code": code}
        try:
            parts = cmd.split()
            p = subprocess.run(parts, cwd=str(workspace), capture_output=True, text=True, timeout=5)
            return {"ok": p.returncode == 0, "data": {"rc": p.returncode, "stdout": p.stdout[:500]}, "decision_code": code}
        except Exception as e:
            return {"ok": False, "error": str(e), "decision_code": code}


class CPSExecutor:
    """Execute CPS (Cognitive Program Sequence) transaction"""
    
    @staticmethod
    def execute(cps: Dict[str, Any], workspace: Path) -> Dict[str, Any]:
        """Execute full CPS and return result with evidence"""
        cps_id = cps.get("cps_id", "unknown")
        objective = cps.get("objective", "")
        ops = cps.get("ops", [])
        expect = cps.get("expect", {})
        
        results = {}
        decision_codes = []
        ok_overall = True
        
        for i, op in enumerate(ops):
            op["_index"] = i
            res = TypedActionDispatcher.dispatch(op, workspace)
            results[f"op_{i}"] = asdict(res)
            decision_codes.append(res.decision_code)
            
            if not res.ok:
                ok_overall = False
                break
        
        # Validate expect conditions
        expect_ok = True
        if expect:
            for key, value in expect.items():
                if key not in results:
                    expect_ok = False
                    decision_codes.append("EXPECT_FAIL")
                    break
        
        # Compute result digest
        result_digest = hashlib.sha256(
            json.dumps(results, sort_keys=True).encode()
        ).hexdigest()
        
        return {
            "cps_id": cps_id,
            "objective": objective,
            "ok": ok_overall and expect_ok,
            "results": results,
            "expect_validated": expect_ok,
            "result_digest": f"sha256:{result_digest}",
            "decision_codes": decision_codes,
            "timestamp_ms": int(time.time() * 1000),
        }

