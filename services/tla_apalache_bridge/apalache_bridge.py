"""TLA+/Apalache invariant bridge — model-checks TLA+ specs if Apalache is available."""
from __future__ import annotations
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


def apalache_available() -> bool:
    return shutil.which("apalache-mc") is not None


@dataclass
class InvariantCheckResult:
    spec_path: str
    invariant: str
    passed: bool
    counterexample: str | None = None
    skipped: bool = False
    skip_reason: str = ""


def check_model_availability() -> bool:
    return apalache_available()


def parse_tla_spec(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {"exists": False, "path": str(path)}
    text = p.read_text(errors="ignore")
    return {
        "exists": True,
        "path": str(path),
        "has_invariants": "Inv" in text or "invariant" in text.lower(),
        "line_count": len(text.splitlines()),
    }


def check_invariant(spec_path: str, invariant: str) -> InvariantCheckResult:
    if not apalache_available():
        return InvariantCheckResult(spec_path, invariant, passed=False,
                                    skipped=True, skip_reason="apalache-mc not installed")
    try:
        result = subprocess.run(
            ["apalache-mc", "check", f"--inv={invariant}", spec_path],
            capture_output=True, text=True, timeout=60,
        )
        passed = result.returncode == 0
        ce = result.stdout if not passed else None
        return InvariantCheckResult(spec_path, invariant, passed=passed, counterexample=ce)
    except subprocess.TimeoutExpired:
        return InvariantCheckResult(spec_path, invariant, passed=False,
                                    skipped=True, skip_reason="timeout")


def get_tla_specs(root: str | Path = ".") -> list[Path]:
    return list(Path(root).rglob("*.tla"))
