"""NVIR Math Oracle — Lean validator with Python-eval + SymPy fallbacks.
© 2026 AXIOLEV Holdings LLC
"""
from __future__ import annotations

import ast
import math
import re
import shutil
import subprocess
import tempfile
import textwrap
from dataclasses import dataclass, field
from typing import Any, Optional


# ── safe eval whitelist ────────────────────────────────────────────────────────

_SAFE_GLOBALS: dict[str, Any] = {
    "__builtins__": {},
    "abs": abs, "round": round, "min": min, "max": max, "sum": sum,
    "pow": pow, "divmod": divmod,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan, "atan2": math.atan2,
    "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
    "sqrt": math.sqrt, "log": math.log, "log2": math.log2, "log10": math.log10,
    "exp": math.exp, "ceil": math.ceil, "floor": math.floor,
    "factorial": math.factorial, "gcd": math.gcd,
    "pi": math.pi, "e": math.e, "inf": math.inf, "tau": math.tau,
    "True": True, "False": False,
}

_SAFE_NODES = frozenset({
    ast.Expression, ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.Compare,
    ast.Call, ast.Constant, ast.IfExp, ast.Attribute,
    ast.Load, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow,
    ast.FloorDiv, ast.BitAnd, ast.BitOr, ast.BitXor,
    ast.And, ast.Or, ast.Not, ast.Invert, ast.UAdd, ast.USub,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.Name, ast.Tuple, ast.List,
})


def _safe_eval(expr: str) -> Any:
    """Evaluate a math expression with no side-effects. Raises ValueError on anything unsafe."""
    expr = expr.strip()
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"syntax: {e}") from e
    for node in ast.walk(tree):
        if type(node) not in _SAFE_NODES:
            raise ValueError(f"unsafe node: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id not in _SAFE_GLOBALS:
            raise ValueError(f"unknown name: {node.id}")
    return eval(compile(tree, "<math_oracle>", "eval"), _SAFE_GLOBALS)  # noqa: S307


# ── LaTeX → Python normaliser ──────────────────────────────────────────────────

_LATEX_MAP = [
    (r"\\cdot|\\times", "*"),
    (r"\\div", "/"),
    (r"\\frac\{([^}]+)\}\{([^}]+)\}", r"(\1)/(\2)"),
    (r"\\sqrt\{([^}]+)\}", r"sqrt(\1)"),
    (r"\\sqrt", "sqrt"),
    (r"\\pi", "pi"),
    (r"\\infty", "inf"),
    (r"\\approx|\\equiv", "=="),
    (r"\\neq|\\ne", "!="),
    (r"\\leq|\\le", "<="),
    (r"\\geq|\\ge", ">="),
    (r"\\left|\\right|\\,|\\;|\\:", ""),
    (r"\$+", ""),
    (r"\\[a-zA-Z]+", ""),  # strip unknown latex commands
]


def _latex_to_python(s: str) -> str:
    for pat, repl in _LATEX_MAP:
        s = re.sub(pat, repl, s)
    return s.strip()


# ── equality tolerance ─────────────────────────────────────────────────────────

_EPS = 1e-9


def _approx_eq(a: Any, b: Any) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if math.isinf(a) and math.isinf(b):
            return a == b
        return abs(a - b) <= _EPS * (1 + abs(a) + abs(b))
    return a == b


# ── verdict dataclass (local, matches oracle.__init__.OracleVerdict interface) ──

@dataclass
class _Verdict:
    valid: bool
    confidence: float
    method: str
    detail: dict = field(default_factory=dict)


# ── layer 1: Python eval ───────────────────────────────────────────────────────

def _try_eval(claim: str) -> Optional[_Verdict]:
    """Attempt direct or LaTeX-cleaned arithmetic validation."""
    for attempt in (claim, _latex_to_python(claim)):
        attempt = attempt.strip()
        if not attempt:
            continue

        # Equation: split on first = that isn't ==, !=, <=, >=
        eq_match = re.search(r"(?<![=!<>])=(?!=)", attempt)
        if eq_match:
            lhs_str = attempt[: eq_match.start()].strip()
            rhs_str = attempt[eq_match.end() :].strip()
            try:
                lhs = _safe_eval(lhs_str)
                rhs = _safe_eval(rhs_str)
                valid = _approx_eq(lhs, rhs)
                return _Verdict(
                    valid=valid, confidence=0.97,
                    method="eval_equation",
                    detail={"lhs": str(lhs)[:50], "rhs": str(rhs)[:50], "equal": valid},
                )
            except (ValueError, TypeError, ZeroDivisionError, OverflowError, RecursionError):
                pass

        # Pure expression — valid if it evaluates without error
        try:
            result = _safe_eval(attempt)
            if result is not None:
                return _Verdict(
                    valid=True, confidence=0.85,
                    method="eval_expression",
                    detail={"result": str(result)[:80]},
                )
        except ZeroDivisionError:
            return _Verdict(
                valid=False, confidence=0.97,
                method="eval_expression",
                detail={"error": "division_by_zero"},
            )
        except (ValueError, TypeError, OverflowError, RecursionError):
            pass

    return None


# ── layer 2: SymPy ─────────────────────────────────────────────────────────────

def _try_sympy(claim: str) -> Optional[_Verdict]:
    try:
        import sympy  # noqa: PLC0415
        from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application  # noqa: PLC0415
        transformations = standard_transformations + (implicit_multiplication_application,)

        cleaned = _latex_to_python(claim)
        eq_match = re.search(r"(?<![=!<>])=(?!=)", cleaned)
        if eq_match:
            lhs_str = cleaned[: eq_match.start()].strip()
            rhs_str = cleaned[eq_match.end() :].strip()
            try:
                lhs = parse_expr(lhs_str, transformations=transformations)
                rhs = parse_expr(rhs_str, transformations=transformations)
                diff = sympy.simplify(lhs - rhs)
                valid = diff == 0
                return _Verdict(
                    valid=valid, confidence=0.99,
                    method="sympy_equation",
                    detail={"diff": str(diff)[:80], "equal": valid},
                )
            except Exception:
                pass

        expr = parse_expr(_latex_to_python(claim), transformations=transformations)
        if expr is not None:
            return _Verdict(
                valid=True, confidence=0.90,
                method="sympy_expression",
                detail={"simplified": str(sympy.simplify(expr))[:80]},
            )
    except Exception:
        pass
    return None


# ── layer 3: Lean subprocess ───────────────────────────────────────────────────

_LEAN_TEMPLATE = textwrap.dedent("""\
    -- NVIR math oracle probe
    #check ({claim})
""")

_LEAN4_TEMPLATE = textwrap.dedent("""\
    -- NVIR math oracle probe
    theorem nvir_check : {claim} := by decide
""")


def _try_lean(claim: str) -> Optional[_Verdict]:
    lean_bin = shutil.which("lean") or shutil.which("lean4")
    if not lean_bin:
        return None
    for template in (_LEAN4_TEMPLATE, _LEAN_TEMPLATE):
        src = template.format(claim=claim)
        with tempfile.NamedTemporaryFile(suffix=".lean", mode="w", delete=False) as f:
            f.write(src)
            tmp = f.name
        try:
            r = subprocess.run(
                [lean_bin, tmp],
                capture_output=True, text=True, timeout=15
            )
            valid = r.returncode == 0
            return _Verdict(
                valid=valid, confidence=0.99,
                method="lean",
                detail={"returncode": r.returncode, "stderr": r.stderr[:200]},
            )
        except subprocess.TimeoutExpired:
            return _Verdict(valid=False, confidence=0.5, method="lean_timeout", detail={})
        except Exception:
            pass
        finally:
            import os; os.unlink(tmp)  # noqa: PLC0415
    return None


# ── layer 4: structural heuristic ─────────────────────────────────────────────

_MATH_TOKENS = re.compile(
    r"[0-9]|[+\-*/^=<>]|"
    r"\b(sin|cos|tan|sqrt|log|exp|abs|pi|inf|sum|integral|derivative|"
    r"theorem|proof|lemma|corollary|forall|exists|iff|implies)\b",
    re.IGNORECASE,
)


def _structural_heuristic(claim: str) -> _Verdict:
    tokens = _MATH_TOKENS.findall(claim)
    n_math = len(tokens)
    length = len(claim.strip())
    valid = n_math >= 1 and length >= 3
    confidence = min(0.65, 0.35 + n_math * 0.05)
    return _Verdict(
        valid=valid, confidence=confidence,
        method="structural",
        detail={"math_tokens": n_math, "length": length},
    )


# ── public oracle class ────────────────────────────────────────────────────────

class MathLeanOracle:
    """Layered math validator: Lean → SymPy → Python eval → structural.

    Tries each layer in order and returns on first definitive result.
    Structural fallback always fires when all others are unavailable.
    """

    def validate(self, claim: str) -> "_VerdictCompat":
        from services.nvir.oracle import OracleVerdict  # noqa: PLC0415
        v = self._validate_internal(claim)
        return OracleVerdict(
            valid=v.valid, confidence=v.confidence,
            method=v.method, detail=v.detail,
        )

    def _validate_internal(self, claim: str) -> _Verdict:
        # Lean first (definitive if available)
        lean = _try_lean(claim)
        if lean is not None:
            return lean
        # SymPy (algebraic)
        sp = _try_sympy(claim)
        if sp is not None and sp.confidence >= 0.95:
            return sp
        # Python eval (arithmetic)
        ev = _try_eval(claim)
        if ev is not None:
            return ev
        # SymPy at lower confidence
        if sp is not None:
            return sp
        # Structural fallback
        return _structural_heuristic(claim)

    def __call__(self, claim: str) -> bool:
        """Convenience: returns verdict.valid for use as a validity_checker callable."""
        return self.validate(claim).valid
