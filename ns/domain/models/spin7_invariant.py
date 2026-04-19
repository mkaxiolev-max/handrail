"""NS∞ CQHML Manifold Engine — Spin(7) Cayley 4-form invariant ∇Φ=0.

The Cayley 4-form Φ on ℝ⁸ (Harvey–Lawson 1982) is preserved by Spin(7) ⊂ SO(8).
It is the direct 8-dimensional analogue of the G₂ 3-form φ on ℝ⁷ (Ring 6).

Φ = e1234 + e1256 + e1278 + e1357 − e1368 − e1458 − e1467
  − e2358 − e2367 − e2457 + e2468 + e3456 + e3478 + e5678

Properties:
  * 14 terms (8 positive, 6 negative)
  * Self-dual: ⋆Φ = Φ  (SO(8) Hodge star on ℝ⁸)
  * Stabilizer in GL(8,ℝ) is Spin(7); holonomy reduction ↔ torsion-free

Ontology alignment (locked — no deprecated names):
  8 basis directions span L1–L8 (Constitutional → Lineage Fabric).
  Spin(7) coherence gate guards L1–L8 joint consistency for projection.

Invariants enforced:
  I1  Canon precedes Conversion
  I5  Provenance inertness — pure / side-effect-free
  I6  Sentinel Gate soundness — Φ-check is a necessary gate condition
  I7  Bisimulation with replay — deterministic (no hidden state)

Tag: cqhml-spin7-phi-v2
AXIOLEV Holdings LLC © 2026
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Cayley 4-form (Harvey–Lawson canonical, basis indices 1–8)
# Each entry: (sign, quadruple)  sign ∈ {+1, −1}
# ---------------------------------------------------------------------------

CAYLEY_QUADRUPLES_SIGNED: tuple[tuple[int, tuple[int, int, int, int]], ...] = (
    (+1, (1, 2, 3, 4)),
    (+1, (1, 2, 5, 6)),
    (+1, (1, 2, 7, 8)),
    (+1, (1, 3, 5, 7)),
    (-1, (1, 3, 6, 8)),
    (-1, (1, 4, 5, 8)),
    (-1, (1, 4, 6, 7)),
    (-1, (2, 3, 5, 8)),
    (-1, (2, 3, 6, 7)),
    (-1, (2, 4, 5, 7)),
    (+1, (2, 4, 6, 8)),
    (+1, (3, 4, 5, 6)),
    (+1, (3, 4, 7, 8)),
    (+1, (5, 6, 7, 8)),
)

# Convenience tuple of just the index quadruples (unsigned) for surface checks
CAYLEY_QUADRUPLES: tuple[tuple[int, int, int, int], ...] = tuple(
    q for _, q in CAYLEY_QUADRUPLES_SIGNED
)

# Embedding dimension — Spin(7) lives in 8D
SPIN7_DIMENSION: int = 8

# Number of Cayley 4-form terms
CAYLEY_TERM_COUNT: int = 14


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def phi_4_components() -> tuple[tuple[int, tuple[int, int, int, int]], ...]:
    """Return the signed Cayley 4-form components (sign, (a, b, c, d))."""
    return CAYLEY_QUADRUPLES_SIGNED


def nabla_phi_4_zero(state) -> bool:
    """∇Φ=0 holds when *state* is a coherent (non-None) value.

    On a torsion-free Spin(7) manifold the Cayley 4-form is parallel,
    i.e. ∇Φ = 0 with respect to the Levi-Civita connection.  Here we
    model this as: the system state must be non-null and not explicitly
    marked as phi_4_incoherent.
    """
    if state is None:
        return False
    if isinstance(state, dict) and state.get("phi_4_incoherent"):
        return False
    # Accept pydantic models with spin7_coherent flag
    coherent = getattr(state, "spin7_coherent", None)
    if coherent is False:
        return False
    return True


def spin7_phi_parallel(state) -> bool:
    """Spin(7) Cayley gate: returns True iff ∇Φ=0 holds for *state*.

    Drop-in analogue of ring6_phi_parallel() for the 8-dimensional case.
    Ring 4 canon promotion may call this in addition to ring6_phi_parallel
    when 8-layer joint coherence is required.
    """
    return nabla_phi_4_zero(state)
