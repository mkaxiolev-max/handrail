"""C06 — MISSING-027: Universal Module Contract tests. I8."""
from services.universal_contract.contract import (
    ContractSpec, ValidationResult, register_contract,
    get_contract, list_contracts, validate_module,
)


def test_contract_registry_has_ns_module():
    assert "ns_module_v1" in list_contracts()


def test_register_new_contract():
    register_contract("test_c", ContractSpec("test_c", "1.0", required_methods=["run"]))
    assert get_contract("test_c") is not None


def test_validate_compliant_module():
    class GoodModule:
        def run(self):
            pass
    register_contract("good", ContractSpec("good", "1.0", required_methods=["run"]))
    result = validate_module(GoodModule(), "good")
    assert result.passed


def test_validate_noncompliant_module():
    class BadModule:
        pass
    register_contract("strict", ContractSpec("strict", "1.0", required_methods=["execute"]))
    result = validate_module(BadModule(), "strict")
    assert not result.passed
    assert "execute" in result.missing_methods


def test_validation_result_is_compliant_property():
    r = ValidationResult("c", True)
    assert r.is_compliant


def test_unknown_contract_fails_gracefully():
    result = validate_module(object(), "nonexistent_contract_xyz")
    assert not result.passed
    assert result.violations


def test_contract_spec_has_version():
    spec = ContractSpec("x", "2.0")
    assert spec.version == "2.0"
