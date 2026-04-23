"""INS-02 NVIR Code Oracle tests. © 2026 AXIOLEV Holdings LLC"""
from __future__ import annotations

import textwrap

import pytest

from services.nvir.oracle.code_unit import (
    CodeUnitOracle,
    _parse,
    _scan_imports,
    _test_function_names,
)


oracle = CodeUnitOracle()


# ── AST utilities ─────────────────────────────────────────────────────────────

def test_code_01_parse_valid_python():
    tree = _parse("x = 1 + 2\nprint(x)")
    assert tree is not None


def test_code_02_parse_syntax_error():
    tree = _parse("def foo(:\n    pass")
    assert tree is None


def test_code_03_scan_blocked_imports_subprocess():
    tree = _parse("import subprocess\nsubprocess.run(['ls'])")
    assert tree is not None
    blocked = _scan_imports(tree)
    assert "subprocess" in blocked


def test_code_04_scan_blocked_imports_socket():
    tree = _parse("import socket\ns = socket.socket()")
    blocked = _scan_imports(tree)
    assert "socket" in blocked


def test_code_05_scan_allowed_imports():
    tree = _parse("import math\nimport json\nimport collections")
    blocked = _scan_imports(tree)
    assert blocked == []


def test_code_06_extract_test_function_names():
    code = textwrap.dedent("""\
        def add(a, b): return a + b
        def test_add(): assert add(1, 2) == 3
        def test_negative(): assert add(-1, -2) == -3
        def helper(): pass
    """)
    tree = _parse(code)
    names = _test_function_names(tree)
    assert "test_add" in names
    assert "test_negative" in names
    assert "helper" not in names
    assert "add" not in names


# ── full validation ────────────────────────────────────────────────────────────

def test_code_07_valid_code_with_passing_tests():
    code = textwrap.dedent("""\
        def multiply(a, b):
            return a * b

        def test_multiply_basic():
            assert multiply(3, 4) == 12

        def test_multiply_zero():
            assert multiply(0, 99) == 0
    """)
    v = oracle.validate(code)
    assert v.valid is True
    assert v.confidence >= 0.95
    assert "exec" in v.method


def test_code_08_invalid_code_with_failing_test():
    code = textwrap.dedent("""\
        def add(a, b):
            return a - b  # intentional bug

        def test_add():
            assert add(2, 3) == 5  # will fail
    """)
    v = oracle.validate(code)
    assert v.valid is False
    assert v.confidence >= 0.95


def test_code_09_syntax_error_rejected():
    v = oracle.validate("def foo(:\n    pass")
    assert v.valid is False
    assert v.confidence == 1.0
    assert "syntax" in v.method


def test_code_10_blocked_import_rejected():
    code = textwrap.dedent("""\
        import subprocess
        def test_safe():
            subprocess.run(['echo', 'hello'])
    """)
    v = oracle.validate(code)
    assert v.valid is False
    assert v.confidence == 1.0
    assert "blocked" in v.method


def test_code_11_plain_script_no_tests():
    code = textwrap.dedent("""\
        result = sum(range(10))
        assert result == 45
    """)
    v = oracle.validate(code)
    assert v.valid is True


def test_code_12_plain_script_with_assertion_error():
    code = textwrap.dedent("""\
        result = sum(range(10))
        assert result == 999  # wrong
    """)
    v = oracle.validate(code)
    assert v.valid is False


def test_code_13_callable_interface():
    good = "x = 1 + 1\nassert x == 2"
    bad = "assert False"
    assert oracle(good) is True
    assert oracle(bad) is False


def test_code_14_verdict_schema():
    from services.nvir.oracle import OracleVerdict
    v = oracle.validate("x = 42")
    assert isinstance(v, OracleVerdict)
    assert isinstance(v.valid, bool)
    assert isinstance(v.confidence, float)
    assert isinstance(v.method, str)
    assert isinstance(v.detail, dict)


def test_code_15_multiple_test_functions_all_pass():
    code = textwrap.dedent("""\
        import math

        def test_sqrt():
            assert abs(math.sqrt(4) - 2.0) < 1e-9

        def test_pi():
            assert math.pi > 3.14

        def test_floor():
            assert math.floor(3.7) == 3
    """)
    v = oracle.validate(code)
    assert v.valid is True
    assert v.detail.get("n_tests", 0) >= 3
