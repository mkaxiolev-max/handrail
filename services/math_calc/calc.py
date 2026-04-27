"""Math calc machine — SymPy symbolic + Z3 constraint solving."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class CalcResult:
    expr: str
    value: Any
    engine: str
    verified: bool


def sympy_simplify(expr_str: str) -> CalcResult:
    try:
        import sympy
        expr = sympy.sympify(expr_str)
        simplified = sympy.simplify(expr)
        return CalcResult(expr=expr_str, value=str(simplified), engine="sympy", verified=True)
    except Exception as e:
        return CalcResult(expr=expr_str, value=None, engine="sympy", verified=False)


def sympy_solve(expr_str: str, var: str = "x") -> CalcResult:
    try:
        import sympy
        x = sympy.Symbol(var)
        solutions = sympy.solve(expr_str, x)
        return CalcResult(expr=expr_str, value=solutions, engine="sympy", verified=True)
    except Exception as e:
        return CalcResult(expr=expr_str, value=None, engine="sympy", verified=False)


def z3_satisfiable(constraints: list[str]) -> CalcResult:
    try:
        import z3
        solver = z3.Solver()
        x = z3.Real("x")
        y = z3.Real("y")
        for c in constraints:
            solver.add(eval(c, {"x": x, "y": y, "z3": z3}))
        result = solver.check()
        sat = str(result) == "sat"
        return CalcResult(expr=str(constraints), value=sat, engine="z3", verified=True)
    except Exception as e:
        return CalcResult(expr=str(constraints), value=None, engine="z3", verified=False)


def numeric_eval(expr_str: str) -> CalcResult:
    try:
        import sympy
        val = float(sympy.sympify(expr_str).evalf())
        return CalcResult(expr=expr_str, value=val, engine="sympy_numeric", verified=True)
    except Exception as e:
        return CalcResult(expr=expr_str, value=None, engine="sympy_numeric", verified=False)
