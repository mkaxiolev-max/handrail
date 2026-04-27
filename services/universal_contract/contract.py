"""Universal Module Contract — 13th ABI: every module declares its contract."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContractSpec:
    name: str
    version: str
    required_methods: list[str] = field(default_factory=list)
    required_attrs: list[str] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    contract_name: str
    passed: bool
    missing_methods: list[str] = field(default_factory=list)
    missing_attrs: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)

    @property
    def is_compliant(self) -> bool:
        return self.passed


_CONTRACTS: dict[str, ContractSpec] = {}


def register_contract(name: str, spec: ContractSpec) -> None:
    _CONTRACTS[name] = spec


def get_contract(name: str) -> ContractSpec | None:
    return _CONTRACTS.get(name)


def list_contracts() -> list[str]:
    return list(_CONTRACTS.keys())


def validate_module(module: Any, contract_name: str) -> ValidationResult:
    spec = _CONTRACTS.get(contract_name)
    if spec is None:
        return ValidationResult(contract_name, False, violations=[f"Contract '{contract_name}' not registered"])
    missing_m = [m for m in spec.required_methods if not callable(getattr(module, m, None))]
    missing_a = [a for a in spec.required_attrs if not hasattr(module, a)]
    passed = not missing_m and not missing_a
    return ValidationResult(contract_name, passed, missing_m, missing_a)


# Register the canonical 13th ABI contract
register_contract("ns_module_v1", ContractSpec(
    name="ns_module_v1",
    version="1.0",
    required_methods=["__init__"],
    required_attrs=[],
    invariants=["module must have docstring", "module must have version"],
))
