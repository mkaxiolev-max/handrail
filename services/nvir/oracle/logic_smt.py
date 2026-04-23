"""NVIR Logic Oracle — Z3 SMT validator with propositional fallback.
© 2026 AXIOLEV Holdings LLC

Verdict semantics:
  valid=True  → formula is SATISFIABLE (could be true under some assignment)
               or is a TAUTOLOGY (always true) — confidence=1.0
  valid=False → formula is UNSATISFIABLE (contradiction) — confidence=1.0
  valid=True, confidence<1.0 → structure valid but satisfiability uncertain
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class _Verdict:
    valid: bool
    confidence: float
    method: str
    detail: dict = field(default_factory=dict)


# ── Z3 layer ───────────────────────────────────────────────────────────────────

# Common variable names available in Z3 evaluation context
_Z3_COMMON_BOOLS = ("A", "B", "C", "D", "P", "Q", "R", "S")
_Z3_COMMON_INTS  = ("x", "y", "z", "n", "m", "k")
_Z3_COMMON_REALS = ("a", "b", "c", "r", "s", "t")


def _build_z3_ns():
    import z3  # noqa: PLC0415
    ns: dict[str, Any] = {
        "__builtins__": {},
        "And": z3.And, "Or": z3.Or, "Not": z3.Not,
        "Implies": z3.Implies, "Xor": z3.Xor, "If": z3.If,
        "Bool": z3.Bool, "Int": z3.Int, "Real": z3.Real,
        "ForAll": z3.ForAll, "Exists": z3.Exists,
        "BoolVal": z3.BoolVal,
        "True": z3.BoolVal(True), "False": z3.BoolVal(False),
        "sat": z3.sat, "unsat": z3.unsat,
    }
    for name in _Z3_COMMON_BOOLS:
        ns[name] = z3.Bool(name)
    for name in _Z3_COMMON_INTS:
        ns[name] = z3.Int(name)
    for name in _Z3_COMMON_REALS:
        ns[name] = z3.Real(name)
    return ns, z3


def _try_z3_python(claim: str) -> Optional[_Verdict]:
    """Parse claim as a Python-style Z3 expression and check sat/tautology."""
    try:
        ns, z3 = _build_z3_ns()
        formula = eval(claim.strip(), ns)  # noqa: S307
        if not isinstance(formula, z3.ExprRef):
            return None

        # Tautology check: ¬formula is UNSAT → formula is always true
        solver_neg = z3.Solver()
        solver_neg.set("timeout", 5000)
        solver_neg.add(z3.Not(formula))
        neg_result = solver_neg.check()
        if neg_result == z3.unsat:
            return _Verdict(
                valid=True, confidence=1.0,
                method="z3_tautology",
                detail={"result": "tautology"},
            )

        # Satisfiability check
        solver = z3.Solver()
        solver.set("timeout", 5000)
        solver.add(formula)
        result = solver.check()
        if result == z3.sat:
            return _Verdict(
                valid=True, confidence=0.90,
                method="z3_sat",
                detail={"result": "satisfiable"},
            )
        if result == z3.unsat:
            return _Verdict(
                valid=False, confidence=1.0,
                method="z3_unsat",
                detail={"result": "unsatisfiable"},
            )
        # unknown
        return _Verdict(
            valid=True, confidence=0.50,
            method="z3_unknown",
            detail={"result": "unknown"},
        )
    except Exception:
        return None


def _try_z3_smt2(claim: str) -> Optional[_Verdict]:
    """Parse claim as SMT-LIB2 format."""
    try:
        import z3  # noqa: PLC0415
        assertions = z3.parse_smt2_string(claim.strip())
        solver = z3.Solver()
        solver.set("timeout", 5000)
        solver.add(assertions)
        result = solver.check()
        if result == z3.sat:
            return _Verdict(
                valid=True, confidence=0.95,
                method="z3_smt2_sat",
                detail={"result": "satisfiable"},
            )
        if result == z3.unsat:
            return _Verdict(
                valid=False, confidence=1.0,
                method="z3_smt2_unsat",
                detail={"result": "unsatisfiable"},
            )
        return _Verdict(
            valid=True, confidence=0.50,
            method="z3_smt2_unknown",
            detail={"result": "unknown"},
        )
    except Exception:
        return None


# ── propositional heuristic layer ──────────────────────────────────────────────

# Known tautology patterns (normalised)
_TAUTOLOGY_RE = [
    re.compile(r"(?i)(true|1)\s*$"),
    re.compile(r"(?i)\b(\w+)\s+(or|v|\|)\s+not\s+\1\b"),
    re.compile(r"(?i)\b(\w+)\s*->\s*\1\b"),
    re.compile(r"(?i)\b(\w+)\s*<=>\s*\1\b"),
    re.compile(r"(?i)\b(\w+)\s+implies\s+\1\b"),
]

# Known contradiction patterns
_CONTRADICT_RE = [
    re.compile(r"(?i)(false|0)\s*$"),
    re.compile(r"(?i)\b(\w+)\s+(and|&|\^)\s+not\s+\1\b"),
    re.compile(r"(?i)\bnot\s+(\w+)\s+(and|&)\s+\1\b"),
]

# Logic operator presence
_LOGIC_TOKENS = re.compile(
    r"(?i)\b(and|or|not|implies|iff|forall|exists|true|false|"
    r"xor|nand|nor|if|then|else|=>|<=>|->|<->|\bv\b|∧|∨|¬|→|↔|∀|∃)\b"
)


def _structural_logic(claim: str) -> _Verdict:
    norm = claim.strip()
    for pat in _CONTRADICT_RE:
        if pat.search(norm):
            return _Verdict(
                valid=False, confidence=0.75,
                method="heuristic_contradiction",
                detail={"pattern": pat.pattern[:60]},
            )
    for pat in _TAUTOLOGY_RE:
        if pat.search(norm):
            return _Verdict(
                valid=True, confidence=0.80,
                method="heuristic_tautology",
                detail={"pattern": pat.pattern[:60]},
            )
    logic_hits = _LOGIC_TOKENS.findall(norm)
    has_logic = len(logic_hits) >= 1
    length_ok = len(norm) >= 3
    valid = has_logic and length_ok
    return _Verdict(
        valid=valid, confidence=0.60 if valid else 0.55,
        method="heuristic_structural",
        detail={"logic_tokens": len(logic_hits), "length": len(norm)},
    )


# ── public oracle class ────────────────────────────────────────────────────────

class LogicSMTOracle:
    """Z3 SMT validator with propositional heuristic fallback.

    Tries:
      1. Z3 Python API (evaluates formula as Z3 ExprRef)
      2. Z3 SMT-LIB2 parser
      3. Structural propositional heuristic
    """

    def validate(self, claim: str) -> "OracleVerdict":
        from services.nvir.oracle import OracleVerdict  # noqa: PLC0415
        v = self._validate_internal(claim)
        return OracleVerdict(
            valid=v.valid, confidence=v.confidence,
            method=v.method, detail=v.detail,
        )

    def _validate_internal(self, claim: str) -> _Verdict:
        # Z3 Python API
        py = _try_z3_python(claim)
        if py is not None:
            return py
        # Z3 SMT-LIB2
        s2 = _try_z3_smt2(claim)
        if s2 is not None:
            return s2
        # Structural fallback
        return _structural_logic(claim)

    def __call__(self, claim: str) -> bool:
        return self.validate(claim).valid
