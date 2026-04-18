"""Ring 6 — G₂ 3-form invariant tests."""
import pytest
from ns.domain.models.g2_invariant import (
    FANO_TRIPLES,
    phi_components,
    nabla_phi_zero,
    ring6_phi_parallel,
)


def test_fano_triples_count():
    assert len(FANO_TRIPLES) == 7


def test_fano_triples_exact():
    expected = ((1,2,3),(1,4,5),(1,6,7),(2,4,6),(2,5,7),(3,4,7),(3,5,6))
    assert FANO_TRIPLES == expected


def test_fano_each_element_in_1_to_7():
    for triple in FANO_TRIPLES:
        for e in triple:
            assert 1 <= e <= 7


def test_fano_each_triple_length_3():
    for triple in FANO_TRIPLES:
        assert len(triple) == 3


def test_phi_components_returns_fano():
    assert phi_components() == FANO_TRIPLES


def test_phi_components_is_tuple():
    assert isinstance(phi_components(), tuple)


def test_nabla_phi_zero_coherent_state():
    assert nabla_phi_zero({"tick": 1}) is True


def test_nabla_phi_zero_string_state():
    assert nabla_phi_zero("active") is True


def test_nabla_phi_zero_int_state():
    assert nabla_phi_zero(0) is True


def test_nabla_phi_zero_none_state():
    assert nabla_phi_zero(None) is False


def test_ring6_phi_parallel_coherent():
    assert ring6_phi_parallel({"tick": 42}) is True


def test_ring6_phi_parallel_none_fails():
    assert ring6_phi_parallel(None) is False


def test_ring6_phi_parallel_empty_dict():
    assert ring6_phi_parallel({}) is True


def test_ring6_phi_parallel_zero():
    assert ring6_phi_parallel(0) is True


def test_ring6_phi_parallel_false_literal():
    assert ring6_phi_parallel(False) is True


def test_fano_all_elements_distinct_per_triple():
    for triple in FANO_TRIPLES:
        assert len(set(triple)) == 3


def test_fano_no_duplicate_triples():
    as_sets = [frozenset(t) for t in FANO_TRIPLES]
    assert len(set(as_sets)) == 7


def test_phi_components_immutable_reference():
    a = phi_components()
    b = phi_components()
    assert a is b or a == b


def test_ring6_importable_surface():
    import ns.domain.models.g2_invariant as m
    assert hasattr(m, "FANO_TRIPLES")
    assert hasattr(m, "phi_components")
    assert hasattr(m, "nabla_phi_zero")
    assert hasattr(m, "ring6_phi_parallel")


def test_fano_covers_all_7_points():
    all_points = set()
    for triple in FANO_TRIPLES:
        all_points.update(triple)
    assert all_points == {1, 2, 3, 4, 5, 6, 7}


def test_each_point_appears_exactly_3_times():
    from collections import Counter
    counts = Counter()
    for triple in FANO_TRIPLES:
        counts.update(triple)
    assert all(v == 3 for v in counts.values())
