"""C16 — Math calc SymPy+Z3 tests. I7."""
from services.math_calc.calc import sympy_simplify, sympy_solve, z3_satisfiable, numeric_eval


def test_simplify_basic():
    r = sympy_simplify("x + x")
    assert r.engine == "sympy"
    assert r.verified


def test_simplify_constant():
    r = sympy_simplify("2 + 3")
    assert r.verified
    assert "5" in str(r.value)


def test_solve_linear():
    r = sympy_solve("x - 5", "x")
    assert r.verified
    assert 5 in r.value or r.value == [5]


def test_numeric_eval():
    r = numeric_eval("2**10")
    assert r.verified
    assert r.value == 1024.0


def test_z3_sat():
    r = z3_satisfiable(["x > 0"])
    assert r.verified
    assert r.value is True


def test_z3_unsat_impossible():
    r = z3_satisfiable(["x > 5", "x < 1"])
    assert r.verified
    assert r.value is False


def test_simplify_returns_calcresult():
    from services.math_calc.calc import CalcResult
    r = sympy_simplify("sin(x)**2 + cos(x)**2")
    assert isinstance(r, CalcResult)
