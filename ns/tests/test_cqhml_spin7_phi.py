"""NS∞ CQHML Manifold Engine — E7 Spin(7) Cayley 4-form Φ tests.

Validates ns/domain/models/spin7_invariant.py:
  * CAYLEY_QUADRUPLES_SIGNED — 14 signed terms (8 positive, 6 negative)
  * CAYLEY_QUADRUPLES — unsigned index quadruples
  * phi_4_components() — returns signed tuples
  * nabla_phi_4_zero(state) — closed-form coherence predicate
  * spin7_phi_parallel(state) — Spin(7) gate (mirrors ring6_phi_parallel)

Locked ontology enforced: Gradient Field, Alexandrian Lexicon, State Manifold,
Alexandrian Archive, Lineage Fabric, Narrative.

Tag: cqhml-spin7-phi-v2
AXIOLEV Holdings LLC © 2026
"""
from __future__ import annotations

import pytest

import ns.domain.models.spin7_invariant as m
from ns.domain.models.spin7_invariant import (
    CAYLEY_QUADRUPLES,
    CAYLEY_QUADRUPLES_SIGNED,
    CAYLEY_TERM_COUNT,
    SPIN7_DIMENSION,
    nabla_phi_4_zero,
    phi_4_components,
    spin7_phi_parallel,
)
from ns.domain.models.g2_invariant import ring6_phi_parallel
from ns.api.schemas.cqhml import (
    DimensionalCoordinate,
    DimensionalEnvelope,
    ObserverFrame,
    PolicyMode,
    SemanticMode,
)


# ---------------------------------------------------------------------------
# 1. Module surface
# ---------------------------------------------------------------------------

def test_importable_surface():
    for name in (
        "CAYLEY_QUADRUPLES_SIGNED",
        "CAYLEY_QUADRUPLES",
        "SPIN7_DIMENSION",
        "CAYLEY_TERM_COUNT",
        "phi_4_components",
        "nabla_phi_4_zero",
        "spin7_phi_parallel",
    ):
        assert hasattr(m, name), f"Missing symbol: {name}"


# ---------------------------------------------------------------------------
# 2. Structural constants
# ---------------------------------------------------------------------------

def test_spin7_dimension_is_8():
    assert SPIN7_DIMENSION == 8


def test_cayley_term_count_constant():
    assert CAYLEY_TERM_COUNT == 14


def test_cayley_quadruples_count():
    """Φ has exactly 14 terms."""
    assert len(CAYLEY_QUADRUPLES_SIGNED) == 14
    assert len(CAYLEY_QUADRUPLES) == 14


def test_cayley_all_four_indices():
    """Every quadruple contains exactly 4 distinct indices, each in 1..8."""
    for q in CAYLEY_QUADRUPLES:
        assert len(q) == 4, f"Not a quadruple: {q}"
        assert len(set(q)) == 4, f"Duplicate index in: {q}"
        for idx in q:
            assert 1 <= idx <= 8, f"Index {idx} out of range in {q}"


def test_cayley_signed_structure():
    """Each signed entry is (sign, quadruple) with sign ∈ {+1, −1}."""
    for sign, q in CAYLEY_QUADRUPLES_SIGNED:
        assert sign in (+1, -1), f"Invalid sign {sign} for {q}"
        assert len(q) == 4


def test_positive_term_count():
    """Φ has exactly 8 positive terms."""
    pos = [s for s, _ in CAYLEY_QUADRUPLES_SIGNED if s == +1]
    assert len(pos) == 8


def test_negative_term_count():
    """Φ has exactly 6 negative terms."""
    neg = [s for s, _ in CAYLEY_QUADRUPLES_SIGNED if s == -1]
    assert len(neg) == 6


def test_cayley_indices_sorted_within_quadruple():
    """Indices within each quadruple are in strictly ascending order (canonical form)."""
    for q in CAYLEY_QUADRUPLES:
        assert list(q) == sorted(q), f"Not sorted: {q}"


def test_cayley_quadruples_unsigned_match_signed():
    """CAYLEY_QUADRUPLES is the unsigned projection of CAYLEY_QUADRUPLES_SIGNED."""
    unsigned = tuple(q for _, q in CAYLEY_QUADRUPLES_SIGNED)
    assert CAYLEY_QUADRUPLES == unsigned


# ---------------------------------------------------------------------------
# 3. phi_4_components()
# ---------------------------------------------------------------------------

def test_phi_4_components_returns_tuple():
    result = phi_4_components()
    assert isinstance(result, tuple)
    assert result is not None


def test_phi_4_components_matches_constant():
    assert phi_4_components() == CAYLEY_QUADRUPLES_SIGNED


# ---------------------------------------------------------------------------
# 4. nabla_phi_4_zero
# ---------------------------------------------------------------------------

def test_nabla_phi_4_zero_none_is_incoherent():
    assert nabla_phi_4_zero(None) is False


def test_nabla_phi_4_zero_coherent_string():
    assert nabla_phi_4_zero("some_state") is True


def test_nabla_phi_4_zero_coherent_dict():
    assert nabla_phi_4_zero({"layer": 4, "tick": 1}) is True


def test_nabla_phi_4_zero_incoherent_dict():
    assert nabla_phi_4_zero({"phi_4_incoherent": True}) is False


def test_nabla_phi_4_zero_explicit_coherent_dict():
    assert nabla_phi_4_zero({"phi_4_incoherent": False}) is True


def test_nabla_phi_4_zero_object_spin7_false():
    class FakeEnvelope:
        spin7_coherent = False

    assert nabla_phi_4_zero(FakeEnvelope()) is False


def test_nabla_phi_4_zero_object_spin7_true():
    class FakeEnvelope:
        spin7_coherent = True

    assert nabla_phi_4_zero(FakeEnvelope()) is True


# ---------------------------------------------------------------------------
# 5. spin7_phi_parallel (main gate)
# ---------------------------------------------------------------------------

def test_spin7_phi_parallel_valid_state():
    assert spin7_phi_parallel("valid_state") is True


def test_spin7_phi_parallel_none():
    assert spin7_phi_parallel(None) is False


def test_spin7_phi_parallel_delegates_to_nabla():
    """spin7_phi_parallel is an alias for nabla_phi_4_zero."""
    state = {"tick": 42}
    assert spin7_phi_parallel(state) == nabla_phi_4_zero(state)


# ---------------------------------------------------------------------------
# 6. Spin(7) ⊇ G₂ coherence relationship
# ---------------------------------------------------------------------------

def test_spin7_subsumes_g2_on_coherent_state():
    """If G₂ φ is parallel, Spin(7) Φ must also be parallel on a coherent state."""
    state = {"layer": 7, "tick": 3}
    # Both gates accept the same coherent state
    assert ring6_phi_parallel(state) is True
    assert spin7_phi_parallel(state) is True


def test_spin7_and_g2_both_reject_none():
    assert ring6_phi_parallel(None) is False
    assert spin7_phi_parallel(None) is False


# ---------------------------------------------------------------------------
# 7. Integration with DimensionalEnvelope
# ---------------------------------------------------------------------------

def _make_envelope(spin7_coherent: bool = True) -> DimensionalEnvelope:
    coord = DimensionalCoordinate(layer=5, tick=1)
    obs = ObserverFrame(frame_id="obs-test", layer=5)
    return DimensionalEnvelope(
        coordinate=coord,
        observer=obs,
        spin7_coherent=spin7_coherent,
        tick=1,
    )


def test_spin7_gate_on_dimensional_envelope_coherent():
    env = _make_envelope(spin7_coherent=True)
    assert spin7_phi_parallel(env) is True


def test_spin7_gate_on_dimensional_envelope_incoherent():
    env = _make_envelope(spin7_coherent=False)
    assert spin7_phi_parallel(env) is False
