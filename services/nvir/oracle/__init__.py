"""NVIR Oracle package — domain-specific validators. © 2026 AXIOLEV Holdings LLC"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .math_lean import MathLeanOracle
from .logic_smt import LogicSMTOracle
from .code_unit import CodeUnitOracle

__all__ = [
    "OracleVerdict",
    "MathLeanOracle",
    "LogicSMTOracle",
    "CodeUnitOracle",
]


@dataclass
class OracleVerdict:
    """Structured result from any domain oracle."""
    valid: bool
    confidence: float          # 0.0–1.0; 1.0 = definitive
    method: str                # e.g. "eval_equation", "z3_tautology", "exec_tests"
    detail: dict = field(default_factory=dict)
