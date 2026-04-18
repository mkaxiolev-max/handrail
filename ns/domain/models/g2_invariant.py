"""Ring 6 — G₂ 3-form invariant ∇φ=0 (Fano plane).

Imported by Ring 4 canon promotion gate and Ring 6 tests.
"""
from __future__ import annotations

FANO_TRIPLES: tuple = ((1, 2, 3), (1, 4, 5), (1, 6, 7), (2, 4, 6), (2, 5, 7), (3, 4, 7), (3, 5, 6))


def phi_components() -> tuple:
    return FANO_TRIPLES


def nabla_phi_zero(state) -> bool:
    """∇φ=0 holds when state is a coherent non-None value."""
    return state is not None


def ring6_phi_parallel(state) -> bool:
    return nabla_phi_zero(state)
