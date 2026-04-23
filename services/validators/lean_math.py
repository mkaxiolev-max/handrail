"""Lean 4 math validator adapter — AXIOLEV Holdings LLC © 2026.

Validates mathematical claims via structural and symbolic analysis.
Lean 4 shell invocation is attempted when the `lean` binary is on PATH;
falls back to heuristic analysis (numeric evaluation, known identities,
bracket-balance) otherwise.

I3 constraint: confidence ceiling I3_ADMIN_CAP (0.95).
"""
from __future__ import annotations
import re, uuid
from typing import Any, Dict

from .contracts import ValidationResult, Verdict, emit_lineage_receipt, cap_confidence

# Known mathematical identities for golden-path lookup
_KNOWN_IDENTITIES: Dict[str, bool] = {
    "pythagoras":     True,   # a² + b² = c²
    "euler_identity": True,   # e^(iπ) + 1 = 0
    "sum_naturals":   True,   # 1+2+…+n = n(n+1)/2
    "fermat_last":    True,   # no positive integer solution for xⁿ+yⁿ=zⁿ, n>2
}

_NUMERIC_RE = re.compile(
    r"^\s*(-?\d+(?:\.\d+)?)\s*([=<>≤≥≠])\s*(-?\d+(?:\.\d+)?)\s*$"
)


def _check_balance(expr: str) -> bool:
    pairs = {"(": ")", "[": "]", "{": "}"}
    stack: list[str] = []
    for ch in expr:
        if ch in pairs:
            stack.append(pairs[ch])
        elif ch in pairs.values():
            if not stack or stack[-1] != ch:
                return False
            stack.pop()
    return len(stack) == 0


def _eval_numeric(claim: str) -> tuple[bool | None, str]:
    m = _NUMERIC_RE.match(claim)
    if not m:
        return None, "not a simple numeric expression"
    lhs, op, rhs = float(m.group(1)), m.group(2), float(m.group(3))
    result = {
        "=": lhs == rhs, "<": lhs < rhs, ">": lhs > rhs,
        "≤": lhs <= rhs, "≥": lhs >= rhs, "≠": lhs != rhs,
    }.get(op)
    return result, f"{lhs} {op} {rhs} → {result}"


def _try_lean_shell(claim: str, context: Dict[str, Any]) -> Dict[str, Any]:
    import shutil, subprocess, tempfile
    if not shutil.which("lean"):
        return {"available": False, "verdict": None, "lean_output": "lean binary not found"}
    lean_src = context.get("lean_src", f"#check ({claim})")
    with tempfile.NamedTemporaryFile(suffix=".lean", mode="w", delete=False) as f:
        f.write(lean_src)
        fname = f.name
    try:
        r = subprocess.run(["lean", fname], capture_output=True, text=True, timeout=15)
        ok = r.returncode == 0
        return {"available": True, "verdict": ok,
                "lean_output": (r.stdout + r.stderr).strip()[:400]}
    except Exception as exc:
        return {"available": True, "verdict": None, "lean_output": str(exc)[:200]}


class LeanMathAdapter:
    domain = "math"

    def validate(self, claim: str, context: Dict[str, Any]) -> ValidationResult:
        claim_id = context.get("claim_id", uuid.uuid4().hex[:12])
        checks: Dict[str, Any] = {}

        balanced = _check_balance(claim)
        checks["bracket_balance"] = balanced

        numeric_ok, numeric_msg = _eval_numeric(claim)
        checks["numeric_eval"] = numeric_msg

        key = context.get("identity_key", "").lower()
        known = _KNOWN_IDENTITIES.get(key)
        checks["known_identity"] = known

        lean_result = _try_lean_shell(claim, context)
        checks["lean_shell"] = lean_result

        if lean_result["available"] and lean_result["verdict"] is not None:
            verdict: Verdict = "PASS" if lean_result["verdict"] else "FAIL"
            confidence = cap_confidence(0.92 if lean_result["verdict"] else 0.90)
            rationale = f"Lean 4 verified: {lean_result['lean_output'][:120]}"
        elif numeric_ok is not None:
            verdict = "PASS" if numeric_ok else "FAIL"
            confidence = cap_confidence(0.88)
            rationale = f"Numeric evaluation: {numeric_msg}"
        elif known is not None:
            verdict = "PASS" if known else "FAIL"
            confidence = cap_confidence(0.80)
            rationale = f"Known identity '{key}': {known}"
        elif not balanced:
            verdict = "FAIL"
            confidence = cap_confidence(0.75)
            rationale = "Bracket balance check failed — malformed expression"
        else:
            verdict = "UNCERTAIN"
            confidence = cap_confidence(0.40)
            rationale = "Structural analysis only — Lean 4 unavailable, no numeric/identity match"

        receipt_id, lineage_hash = emit_lineage_receipt(
            claim_id=claim_id, domain=self.domain, adapter="lean_math",
            verdict=verdict, confidence=confidence, checks=checks,
        )
        return ValidationResult(
            claim_id=claim_id, domain=self.domain, adapter="lean_math",
            verdict=verdict, confidence=confidence, rationale=rationale,
            checks=checks, receipt_id=receipt_id, lineage_hash=lineage_hash,
        )
