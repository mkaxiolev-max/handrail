"""NVIR — Novel Valid Insight Rate. © 2026 AXIOLEV Holdings LLC"""
from .loop import (
    Candidate, Island, NovelyOracle, ValidityOracle, IrreducibilityOracle,
    NvirScorer, EvolutionaryLoop, run_generation,
)
from .generator import (
    GeneratorSeed, GeneratedCandidate,
    ModelDispatcher, MockDispatcher, NSLocalDispatcher, AnthropicDispatcher,
    CompositeDispatcher, NVIRGenerator,
)
from .dispatcher import VerificationReceipt, NVIRDispatcher
from .oracle import OracleVerdict, MathLeanOracle, LogicSMTOracle, CodeUnitOracle

__all__ = [
    # loop primitives
    "Candidate", "Island", "NovelyOracle", "ValidityOracle", "IrreducibilityOracle",
    "NvirScorer", "EvolutionaryLoop", "run_generation",
    # generator
    "GeneratorSeed", "GeneratedCandidate",
    "ModelDispatcher", "MockDispatcher", "NSLocalDispatcher", "AnthropicDispatcher",
    "CompositeDispatcher", "NVIRGenerator",
    # dispatcher
    "VerificationReceipt", "NVIRDispatcher",
    # oracles
    "OracleVerdict", "MathLeanOracle", "LogicSMTOracle", "CodeUnitOracle",
]
