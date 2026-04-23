"""NVIR Code Oracle — generated-code unit-test validator.
© 2026 AXIOLEV Holdings LLC

Validation pipeline:
  1. AST parse check (syntax)
  2. Blocked-import scan (security boundary)
  3. subprocess execution with timeout
     a. If test functions present → run pytest/unittest
     b. Otherwise → run as plain script
  4. Return OracleVerdict based on exit code + output
"""
from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass, field
from typing import Optional


# ── security: blocked import roots ────────────────────────────────────────────

# These modules are blocked in TESTED code (not in the oracle itself).
_BLOCKED_ROOTS = frozenset({
    "subprocess", "ctypes", "cffi", "mmap",
    "socket", "ssl", "http", "urllib", "requests", "httpx",
    "ftplib", "telnetlib", "smtplib", "poplib", "imaplib",
    "pickle", "marshal", "shelve",
    "pty", "tty", "termios",
    "resource", "signal",
})

_EXEC_TIMEOUT = 10  # seconds


@dataclass
class _Verdict:
    valid: bool
    confidence: float
    method: str
    detail: dict = field(default_factory=dict)


# ── AST utilities ──────────────────────────────────────────────────────────────

def _parse(code: str) -> Optional[ast.Module]:
    """Return AST or None on syntax error."""
    try:
        return ast.parse(code)
    except SyntaxError:
        return None


def _scan_imports(tree: ast.Module) -> list[str]:
    """Return list of blocked import roots found in the code."""
    blocked: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in _BLOCKED_ROOTS:
                    blocked.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                if root in _BLOCKED_ROOTS:
                    blocked.append(node.module)
    return blocked


def _test_function_names(tree: ast.Module) -> list[str]:
    """Return names of top-level functions starting with test_."""
    return [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    ]


# ── subprocess runner ─────────────────────────────────────────────────────────

def _run_code(code: str, has_tests: bool) -> tuple[int, str, str]:
    """Write code to temp file and run it. Returns (returncode, stdout, stderr)."""
    # Prepend a no-network sentinel so any socket attempt is caught at import time
    sentinel = textwrap.dedent("""\
        import sys as _sys
        _sys.modules.setdefault('socket', type(_sys)('socket'))
    """)
    full_code = sentinel + "\n" + code

    with tempfile.NamedTemporaryFile(
        suffix=".py", mode="w", delete=False, dir=tempfile.gettempdir()
    ) as f:
        f.write(full_code)
        tmp = f.name

    try:
        if has_tests:
            # Try pytest first, fall back to unittest discover
            cmd_pytest = [sys.executable, "-m", "pytest", tmp, "-x", "-q", "--tb=short"]
            cmd_unittest = [sys.executable, "-m", "unittest", tmp]
            for cmd in (cmd_pytest, cmd_unittest):
                try:
                    r = subprocess.run(
                        cmd, capture_output=True, text=True, timeout=_EXEC_TIMEOUT
                    )
                    if r.returncode in (0, 1):  # pytest: 0=pass 1=fail 2=interrupted
                        return r.returncode, r.stdout, r.stderr
                except FileNotFoundError:
                    continue
                except subprocess.TimeoutExpired:
                    return -1, "", "timeout"
        # Plain script
        r = subprocess.run(
            [sys.executable, tmp],
            capture_output=True, text=True, timeout=_EXEC_TIMEOUT,
        )
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


# ── test harness injection ────────────────────────────────────────────────────

def _inject_test_runner(code: str, test_names: list[str]) -> str:
    """Append a __main__ block that calls each test function and reports pass/fail."""
    calls = "\n".join(f"    {name}()" for name in test_names)
    harness = textwrap.dedent(f"""\

        if __name__ == "__main__":
            _failures = []
            _tests = [{", ".join(repr(n) for n in test_names)}]
            for _name in _tests:
                try:
                    globals()[_name]()
                except Exception as _e:
                    _failures.append(f"FAIL {{_name}}: {{_e}}")
            if _failures:
                for _f in _failures:
                    print(_f)
                raise SystemExit(1)
            print(f"OK {{len(_tests)}} tests passed")
    """)
    return code + harness


# ── public oracle ─────────────────────────────────────────────────────────────

class CodeUnitOracle:
    """Validates generated Python code by static analysis + subprocess execution.

    For code with test_ functions: runs them and requires all to pass.
    For plain code: requires no syntax errors, no blocked imports, exits 0.
    """

    def __init__(self, timeout: int = _EXEC_TIMEOUT):
        self.timeout = timeout

    def validate(self, code: str) -> "OracleVerdict":
        from services.nvir.oracle import OracleVerdict  # noqa: PLC0415
        v = self._validate_internal(code)
        return OracleVerdict(
            valid=v.valid, confidence=v.confidence,
            method=v.method, detail=v.detail,
        )

    def _validate_internal(self, code: str) -> _Verdict:
        # Layer 1: AST parse
        tree = _parse(code)
        if tree is None:
            return _Verdict(
                valid=False, confidence=1.0,
                method="ast_syntax_error",
                detail={"error": "SyntaxError"},
            )

        # Layer 2: blocked imports
        blocked = _scan_imports(tree)
        if blocked:
            return _Verdict(
                valid=False, confidence=1.0,
                method="blocked_import",
                detail={"blocked": blocked[:5]},
            )

        # Layer 3: detect test functions
        test_names = _test_function_names(tree)
        has_tests = len(test_names) > 0

        # Inject runner harness if tests found but no __main__
        run_code = code
        if has_tests and "__main__" not in code:
            run_code = _inject_test_runner(code, test_names)

        # Layer 4: execute
        rc, stdout, stderr = _run_code(run_code, has_tests)

        if rc == -1:  # timeout
            return _Verdict(
                valid=False, confidence=0.90,
                method="exec_timeout",
                detail={"timeout_sec": self.timeout},
            )

        valid = rc == 0
        method = "exec_tests" if has_tests else "exec_script"
        return _Verdict(
            valid=valid, confidence=0.98,
            method=method,
            detail={
                "returncode": rc,
                "n_tests": len(test_names),
                "stdout": stdout[:300],
                "stderr": stderr[:200],
            },
        )

    def __call__(self, code: str) -> bool:
        return self.validate(code).valid
