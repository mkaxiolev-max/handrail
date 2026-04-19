"""NS∞ CQHML Manifold Engine — E3 quaternion core tests (pure NumPy).

Tag: cqhml-quaternion-core-v2
AXIOLEV Holdings LLC © 2026
"""
import math
import pytest
import numpy as np

from ns.services.cqhml.quaternion import (
    Quaternion,
    identity,
    from_axis_angle,
    from_components,
    slerp,
    layer_rotation,
    phi_coherent,
    ensure_positive_hemisphere,
    compose_layer_path,
)


# ---------------------------------------------------------------------------
# Module surface
# ---------------------------------------------------------------------------

def test_importable_surface():
    import ns.services.cqhml.quaternion as m
    for name in (
        "Quaternion", "identity", "from_axis_angle", "from_components",
        "slerp", "layer_rotation", "phi_coherent",
        "ensure_positive_hemisphere", "compose_layer_path",
    ):
        assert hasattr(m, name), f"Missing: {name}"


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_construction_components():
    q = Quaternion(1.0, 2.0, 3.0, 4.0)
    assert q.w == pytest.approx(1.0)
    assert q.x == pytest.approx(2.0)
    assert q.y == pytest.approx(3.0)
    assert q.z == pytest.approx(4.0)


def test_components_property_returns_copy():
    q = Quaternion(1.0, 0.0, 0.0, 0.0)
    arr = q.components
    arr[0] = 999.0
    assert q.w == pytest.approx(1.0)  # original unchanged


def test_from_components():
    arr = np.array([1.0, 0.0, 0.0, 0.0])
    q = from_components(arr)
    assert q == identity()


def test_from_components_wrong_shape():
    with pytest.raises(ValueError):
        from_components(np.array([1.0, 0.0, 0.0]))


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------

def test_identity_components():
    q = identity()
    assert q.w == pytest.approx(1.0)
    assert q.x == pytest.approx(0.0)
    assert q.y == pytest.approx(0.0)
    assert q.z == pytest.approx(0.0)


def test_identity_norm():
    assert identity().norm() == pytest.approx(1.0)


def test_identity_is_unit():
    q = identity()
    assert phi_coherent(q)


# ---------------------------------------------------------------------------
# Norm / normalize
# ---------------------------------------------------------------------------

def test_norm_basic():
    q = Quaternion(1.0, 0.0, 0.0, 0.0)
    assert q.norm() == pytest.approx(1.0)


def test_norm_computed():
    q = Quaternion(1.0, 2.0, 3.0, 4.0)
    expected = math.sqrt(1 + 4 + 9 + 16)
    assert q.norm() == pytest.approx(expected)


def test_norm_squared():
    q = Quaternion(1.0, 2.0, 3.0, 4.0)
    assert q.norm_squared() == pytest.approx(30.0)


def test_normalize_produces_unit():
    q = Quaternion(1.0, 2.0, 3.0, 4.0).normalize()
    assert q.norm() == pytest.approx(1.0, abs=1e-12)


def test_normalize_direction_preserved():
    q = Quaternion(3.0, 0.0, 0.0, 0.0).normalize()
    assert q.w == pytest.approx(1.0)
    assert q.x == pytest.approx(0.0)


def test_normalize_zero_raises():
    with pytest.raises(ValueError):
        Quaternion(0.0, 0.0, 0.0, 0.0).normalize()


# ---------------------------------------------------------------------------
# Conjugate
# ---------------------------------------------------------------------------

def test_conjugate_negates_vector_part():
    q = Quaternion(1.0, 2.0, 3.0, 4.0)
    c = q.conjugate()
    assert c.w == pytest.approx(1.0)
    assert c.x == pytest.approx(-2.0)
    assert c.y == pytest.approx(-3.0)
    assert c.z == pytest.approx(-4.0)


def test_conjugate_of_conjugate_is_self():
    q = Quaternion(1.0, 2.0, 3.0, 4.0)
    assert q.conjugate().conjugate() == q


def test_q_times_conjugate_is_norm_squared_times_identity():
    q = Quaternion(1.0, 2.0, 3.0, 4.0)
    result = q * q.conjugate()
    expected_w = q.norm_squared()
    assert result.w == pytest.approx(expected_w, rel=1e-9)
    assert result.x == pytest.approx(0.0, abs=1e-9)
    assert result.y == pytest.approx(0.0, abs=1e-9)
    assert result.z == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# Inverse
# ---------------------------------------------------------------------------

def test_inverse_unit_quaternion_equals_conjugate():
    q = from_axis_angle(np.array([0.0, 0.0, 1.0]), math.pi / 4)
    inv = q.inverse()
    conj = q.conjugate()
    assert inv == conj


def test_q_times_inverse_is_identity():
    q = Quaternion(1.0, 2.0, 3.0, 4.0)
    result = q * q.inverse()
    assert result.w == pytest.approx(1.0, abs=1e-9)
    assert result.x == pytest.approx(0.0, abs=1e-9)
    assert result.y == pytest.approx(0.0, abs=1e-9)
    assert result.z == pytest.approx(0.0, abs=1e-9)


def test_inverse_zero_raises():
    with pytest.raises(ValueError):
        Quaternion(0.0, 0.0, 0.0, 0.0).inverse()


# ---------------------------------------------------------------------------
# Multiplication — Hamilton product
# ---------------------------------------------------------------------------

def test_multiply_identity_left():
    q = Quaternion(0.5, 0.5, 0.5, 0.5)
    assert identity() * q == q


def test_multiply_identity_right():
    q = Quaternion(0.5, 0.5, 0.5, 0.5)
    assert q * identity() == q


def test_multiply_known_result():
    # i * j = k
    i = Quaternion(0.0, 1.0, 0.0, 0.0)
    j = Quaternion(0.0, 0.0, 1.0, 0.0)
    k = Quaternion(0.0, 0.0, 0.0, 1.0)
    assert i * j == k


def test_multiply_non_commutative():
    # j * i = -k
    i = Quaternion(0.0, 1.0, 0.0, 0.0)
    j = Quaternion(0.0, 0.0, 1.0, 0.0)
    k = Quaternion(0.0, 0.0, 0.0, 1.0)
    assert j * i == -k


def test_multiply_associative():
    q1 = Quaternion(1.0, 2.0, 3.0, 4.0).normalize()
    q2 = Quaternion(0.5, -0.5, 0.5, -0.5).normalize()
    q3 = from_axis_angle(np.array([1.0, 1.0, 0.0]), math.pi / 3).normalize()
    left = (q1 * q2) * q3
    right = q1 * (q2 * q3)
    assert left == right


def test_negation():
    q = Quaternion(1.0, 2.0, 3.0, 4.0)
    neg = -q
    assert neg.w == pytest.approx(-1.0)
    assert neg.x == pytest.approx(-2.0)


# ---------------------------------------------------------------------------
# from_axis_angle
# ---------------------------------------------------------------------------

def test_from_axis_angle_identity_at_zero():
    q = from_axis_angle(np.array([0.0, 1.0, 0.0]), 0.0)
    assert q == identity()


def test_from_axis_angle_180_degrees():
    q = from_axis_angle(np.array([0.0, 0.0, 1.0]), math.pi)
    # w = cos(pi/2) = 0, z = sin(pi/2) = 1
    assert q.w == pytest.approx(0.0, abs=1e-9)
    assert q.z == pytest.approx(1.0, abs=1e-9)


def test_from_axis_angle_normalises_axis():
    q1 = from_axis_angle(np.array([0.0, 1.0, 0.0]), math.pi / 2)
    q2 = from_axis_angle(np.array([0.0, 5.0, 0.0]), math.pi / 2)
    assert q1 == q2


def test_from_axis_angle_zero_axis_raises():
    with pytest.raises(ValueError):
        from_axis_angle(np.array([0.0, 0.0, 0.0]), math.pi / 4)


def test_from_axis_angle_produces_unit():
    q = from_axis_angle(np.array([1.0, 2.0, 3.0]), 1.234)
    assert q.norm() == pytest.approx(1.0, abs=1e-12)


# ---------------------------------------------------------------------------
# Vector rotation
# ---------------------------------------------------------------------------

def test_rotate_identity_leaves_vector_unchanged():
    v = np.array([1.0, 2.0, 3.0])
    result = identity().rotate(v)
    np.testing.assert_allclose(result, v, atol=1e-12)


def test_rotate_90_degrees_around_z():
    q = from_axis_angle(np.array([0.0, 0.0, 1.0]), math.pi / 2)
    v = np.array([1.0, 0.0, 0.0])
    result = q.rotate(v)
    np.testing.assert_allclose(result, [0.0, 1.0, 0.0], atol=1e-12)


def test_rotate_180_degrees_around_y():
    q = from_axis_angle(np.array([0.0, 1.0, 0.0]), math.pi)
    v = np.array([1.0, 0.0, 0.0])
    result = q.rotate(v)
    np.testing.assert_allclose(result, [-1.0, 0.0, 0.0], atol=1e-12)


def test_rotate_preserves_vector_length():
    q = from_axis_angle(np.array([1.0, 2.0, 3.0]), 0.7)
    v = np.array([3.0, -1.0, 2.0])
    result = q.rotate(v)
    assert np.linalg.norm(result) == pytest.approx(np.linalg.norm(v), abs=1e-11)


def test_rotate_wrong_shape_raises():
    with pytest.raises(ValueError):
        identity().rotate(np.array([1.0, 2.0]))


# ---------------------------------------------------------------------------
# to_rotation_matrix
# ---------------------------------------------------------------------------

def test_rotation_matrix_shape():
    M = identity().to_rotation_matrix()
    assert M.shape == (3, 3)


def test_rotation_matrix_identity():
    M = identity().to_rotation_matrix()
    np.testing.assert_allclose(M, np.eye(3), atol=1e-12)


def test_rotation_matrix_orthogonal():
    q = from_axis_angle(np.array([1.0, 2.0, 3.0]), 1.1)
    M = q.to_rotation_matrix()
    np.testing.assert_allclose(M @ M.T, np.eye(3), atol=1e-11)


def test_rotation_matrix_det_one():
    q = from_axis_angle(np.array([1.0, 0.0, 1.0]), 2.0)
    M = q.to_rotation_matrix()
    assert np.linalg.det(M) == pytest.approx(1.0, abs=1e-11)


def test_rotation_matrix_consistent_with_rotate():
    q = from_axis_angle(np.array([0.0, 1.0, 0.0]), math.pi / 3)
    v = np.array([2.0, -1.0, 0.5])
    via_quat = q.rotate(v)
    via_mat = q.to_rotation_matrix() @ v
    np.testing.assert_allclose(via_quat, via_mat, atol=1e-11)


# ---------------------------------------------------------------------------
# Angle / axis extraction
# ---------------------------------------------------------------------------

def test_angle_extraction():
    angle = math.pi / 4
    q = from_axis_angle(np.array([0.0, 1.0, 0.0]), angle)
    assert q.angle() == pytest.approx(angle, abs=1e-11)


def test_axis_extraction():
    ax = np.array([1.0, 0.0, 0.0])
    q = from_axis_angle(ax, 1.0)
    np.testing.assert_allclose(q.axis(), ax, atol=1e-11)


def test_identity_angle_is_zero():
    assert identity().angle() == pytest.approx(0.0, abs=1e-12)


# ---------------------------------------------------------------------------
# SLERP
# ---------------------------------------------------------------------------

def test_slerp_t0_returns_q1():
    q1 = from_axis_angle(np.array([0.0, 1.0, 0.0]), 0.3)
    q2 = from_axis_angle(np.array([0.0, 1.0, 0.0]), 1.2)
    result = slerp(q1, q2, 0.0)
    assert result == q1


def test_slerp_t1_returns_q2():
    q1 = from_axis_angle(np.array([0.0, 1.0, 0.0]), 0.3)
    q2 = from_axis_angle(np.array([0.0, 1.0, 0.0]), 1.2)
    result = slerp(q1, q2, 1.0)
    assert result == q2


def test_slerp_midpoint_is_unit():
    q1 = from_axis_angle(np.array([1.0, 0.0, 0.0]), 0.0)
    q2 = from_axis_angle(np.array([1.0, 0.0, 0.0]), math.pi / 2)
    mid = slerp(q1, q2, 0.5)
    assert mid.norm() == pytest.approx(1.0, abs=1e-11)


def test_slerp_midpoint_angle():
    ax = np.array([0.0, 0.0, 1.0])
    q1 = from_axis_angle(ax, 0.0)
    q2 = from_axis_angle(ax, math.pi / 2)
    mid = slerp(q1, q2, 0.5)
    assert mid.angle() == pytest.approx(math.pi / 4, abs=1e-10)


def test_slerp_t_out_of_range_raises():
    q1 = identity()
    q2 = identity()
    with pytest.raises(ValueError):
        slerp(q1, q2, -0.1)
    with pytest.raises(ValueError):
        slerp(q1, q2, 1.1)


def test_slerp_identical_quaternions():
    q = from_axis_angle(np.array([1.0, 0.0, 0.0]), 0.5)
    result = slerp(q, q, 0.5)
    assert result.norm() == pytest.approx(1.0, abs=1e-11)


# ---------------------------------------------------------------------------
# layer_rotation — CQHML manifold helpers
# ---------------------------------------------------------------------------

def test_layer_rotation_identity_same_layer():
    q = layer_rotation(5, 5)
    assert q == identity()


def test_layer_rotation_produces_unit_quaternion():
    for src in (1, 3, 7):
        for tgt in (1, 5, 10):
            q = layer_rotation(src, tgt)
            assert q.norm() == pytest.approx(1.0, abs=1e-12), f"Failed for {src}->{tgt}"


def test_layer_rotation_angle_formula():
    # angle = (target - source) * pi / 20
    src, tgt = 1, 6
    expected_angle = abs(tgt - src) * math.pi / 20.0
    q = layer_rotation(src, tgt)
    assert q.angle() == pytest.approx(expected_angle, abs=1e-11)


def test_layer_rotation_inverse_symmetry():
    # layer_rotation(a, b) * layer_rotation(b, a) ≈ identity
    q_fwd = layer_rotation(3, 8)
    q_bwd = layer_rotation(8, 3)
    result = q_fwd * q_bwd
    assert result == identity()


def test_layer_rotation_out_of_range_raises():
    with pytest.raises(ValueError):
        layer_rotation(0, 5)
    with pytest.raises(ValueError):
        layer_rotation(1, 11)


def test_layer_rotation_all_boundary_pairs():
    layer_rotation(1, 10)
    layer_rotation(10, 1)
    layer_rotation(1, 1)
    layer_rotation(10, 10)


# ---------------------------------------------------------------------------
# phi_coherent — G₂ 3-form coherence
# ---------------------------------------------------------------------------

def test_phi_coherent_identity():
    assert phi_coherent(identity()) is True


def test_phi_coherent_unit_positive_w():
    q = from_axis_angle(np.array([0.0, 1.0, 0.0]), math.pi / 6)
    assert q.w > 0
    assert phi_coherent(q) is True


def test_phi_coherent_non_unit_fails():
    q = Quaternion(2.0, 0.0, 0.0, 0.0)
    assert phi_coherent(q) is False


def test_phi_coherent_negative_w_fails():
    # w < 0 means negative hemisphere
    q = Quaternion(-1.0, 0.0, 0.0, 0.0)
    assert phi_coherent(q) is False


def test_phi_coherent_zero_w_passes():
    # w == 0, unit quaternion: 180-degree rotation — on the equator
    q = Quaternion(0.0, 1.0, 0.0, 0.0)
    assert phi_coherent(q) is True


# ---------------------------------------------------------------------------
# ensure_positive_hemisphere
# ---------------------------------------------------------------------------

def test_ensure_positive_hemisphere_no_op_for_positive_w():
    q = from_axis_angle(np.array([0.0, 1.0, 0.0]), math.pi / 4)
    assert q.w > 0
    result = ensure_positive_hemisphere(q)
    assert result == q


def test_ensure_positive_hemisphere_negates_negative_w():
    q = from_axis_angle(np.array([0.0, 1.0, 0.0]), 1.8 * math.pi)
    # This quaternion has w < 0
    result = ensure_positive_hemisphere(q)
    assert result.w >= 0.0


def test_ensure_positive_hemisphere_is_still_unit():
    q = Quaternion(-0.5, -0.5, -0.5, -0.5)
    result = ensure_positive_hemisphere(q)
    assert result.norm() == pytest.approx(1.0, abs=1e-11)
    assert result.w >= 0.0


# ---------------------------------------------------------------------------
# compose_layer_path
# ---------------------------------------------------------------------------

def test_compose_layer_path_two_steps():
    # path [1, 5, 10] should equal layer_rotation(1,5) * layer_rotation(5,10)
    result = compose_layer_path([1, 5, 10])
    expected = layer_rotation(1, 5) * layer_rotation(5, 10)
    assert result == expected


def test_compose_layer_path_single_step():
    result = compose_layer_path([2, 7])
    expected = layer_rotation(2, 7)
    assert result == expected


def test_compose_layer_path_identity_path():
    result = compose_layer_path([5, 5])
    assert result == identity()


def test_compose_layer_path_too_short_raises():
    with pytest.raises(ValueError):
        compose_layer_path([5])


def test_compose_layer_path_produces_unit():
    result = compose_layer_path([1, 3, 7, 10])
    assert result.norm() == pytest.approx(1.0, abs=1e-11)


# ---------------------------------------------------------------------------
# Ontology invariants
# ---------------------------------------------------------------------------

def test_i5_provenance_all_ops_pure():
    """I5: quaternion ops must be pure (no mutation of inputs)."""
    q1 = Quaternion(1.0, 0.0, 0.0, 0.0)
    q2 = Quaternion(0.0, 1.0, 0.0, 0.0)
    _ = q1 * q2
    _ = q1.conjugate()
    _ = q1.inverse()
    _ = q1.normalize()
    assert q1.w == pytest.approx(1.0)
    assert q1.x == pytest.approx(0.0)


def test_layer_rotations_cover_all_10_layers():
    """All 10 ontology layers must admit valid layer_rotation calls."""
    for src in range(1, 11):
        for tgt in range(1, 11):
            q = layer_rotation(src, tgt)
            assert q.norm() == pytest.approx(1.0, abs=1e-12)


def test_no_deprecated_names_in_module():
    """Locked ontology: deprecated names must not appear as public symbols."""
    import ns.services.cqhml.quaternion as m
    deprecated = {"Ether", "Lexicon", "Manifold", "Alexandria", "CTF", "Storytime"}
    public = {name for name in dir(m) if not name.startswith("_")}
    assert not deprecated.intersection(public)


def test_phi_coherent_all_layer_rotations():
    """Every canonical layer_rotation should be G₂-coherent (positive hemisphere)."""
    for src in range(1, 11):
        for tgt in range(src, 11):
            q = layer_rotation(src, tgt)
            q_canon = ensure_positive_hemisphere(q)
            assert phi_coherent(q_canon), f"Not phi_coherent for {src}->{tgt}"
