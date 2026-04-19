"""NS∞ CQHML Manifold Engine — quaternion core (pure NumPy).

Tag: cqhml-quaternion-core-v2
AXIOLEV Holdings LLC © 2026

Quaternions encode rotations between ontology layers (L1–L10).
G₂ coherence: unit quaternion with w ≥ 0 (positive hemisphere convention).
I5 (provenance inertness): all operations are pure / side-effect-free.
"""
from __future__ import annotations

import math
import numpy as np


class Quaternion:
    """Hamilton quaternion q = w + xi + yj + zk backed by a NumPy float64 array."""

    __slots__ = ("_q",)

    def __init__(self, w: float, x: float, y: float, z: float) -> None:
        self._q = np.array([w, x, y, z], dtype=np.float64)

    # ------------------------------------------------------------------
    # Components
    # ------------------------------------------------------------------

    @property
    def w(self) -> float:
        return float(self._q[0])

    @property
    def x(self) -> float:
        return float(self._q[1])

    @property
    def y(self) -> float:
        return float(self._q[2])

    @property
    def z(self) -> float:
        return float(self._q[3])

    @property
    def components(self) -> np.ndarray:
        return self._q.copy()

    # ------------------------------------------------------------------
    # Arithmetic
    # ------------------------------------------------------------------

    def __mul__(self, other: "Quaternion") -> "Quaternion":
        """Hamilton product (non-commutative)."""
        w1, x1, y1, z1 = self.w, self.x, self.y, self.z
        w2, x2, y2, z2 = other.w, other.x, other.y, other.z
        return Quaternion(
            w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        )

    def __add__(self, other: "Quaternion") -> "Quaternion":
        return Quaternion(*(self._q + other._q))

    def __neg__(self) -> "Quaternion":
        return Quaternion(*(-self._q))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Quaternion):
            return NotImplemented
        return bool(np.allclose(self._q, other._q, atol=1e-9))

    def __repr__(self) -> str:
        return (
            f"Quaternion(w={self.w:.8f}, x={self.x:.8f}, "
            f"y={self.y:.8f}, z={self.z:.8f})"
        )

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def norm(self) -> float:
        return float(np.linalg.norm(self._q))

    def norm_squared(self) -> float:
        return float(np.dot(self._q, self._q))

    def normalize(self) -> "Quaternion":
        n = self.norm()
        if n < 1e-15:
            raise ValueError("Cannot normalize zero quaternion")
        return Quaternion(*(self._q / n))

    def conjugate(self) -> "Quaternion":
        return Quaternion(self.w, -self.x, -self.y, -self.z)

    def inverse(self) -> "Quaternion":
        n2 = self.norm_squared()
        if n2 < 1e-30:
            raise ValueError("Cannot invert zero quaternion")
        return Quaternion(
            self.w / n2,
            -self.x / n2,
            -self.y / n2,
            -self.z / n2,
        )

    def dot(self, other: "Quaternion") -> float:
        return float(np.dot(self._q, other._q))

    # ------------------------------------------------------------------
    # Rotation
    # ------------------------------------------------------------------

    def rotate(self, v: np.ndarray) -> np.ndarray:
        """Rotate 3-vector v by this unit quaternion: q v q*."""
        v = np.asarray(v, dtype=np.float64)
        if v.shape != (3,):
            raise ValueError("rotate() requires a 3-element vector")
        qv = Quaternion(0.0, v[0], v[1], v[2])
        result = self * qv * self.conjugate()
        return np.array([result.x, result.y, result.z])

    def to_rotation_matrix(self) -> np.ndarray:
        """Return the 3×3 rotation matrix for this unit quaternion."""
        q = self.normalize()
        w, x, y, z = q.w, q.x, q.y, q.z
        return np.array(
            [
                [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
            ],
            dtype=np.float64,
        )

    # ------------------------------------------------------------------
    # Angle extraction
    # ------------------------------------------------------------------

    def angle(self) -> float:
        """Return the rotation angle (radians) for this unit quaternion."""
        q = self.normalize()
        w_clamped = float(np.clip(q.w, -1.0, 1.0))
        return 2.0 * math.acos(abs(w_clamped))

    def axis(self) -> np.ndarray:
        """Return the unit rotation axis; returns [0,1,0] for identity."""
        q = self.normalize()
        s = math.sqrt(max(0.0, 1.0 - q.w * q.w))
        if s < 1e-10:
            return np.array([0.0, 1.0, 0.0])
        return np.array([q.x / s, q.y / s, q.z / s])


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------

def identity() -> Quaternion:
    return Quaternion(1.0, 0.0, 0.0, 0.0)


def from_axis_angle(axis: np.ndarray, angle: float) -> Quaternion:
    """Construct a unit quaternion encoding a rotation of `angle` radians about `axis`."""
    axis = np.asarray(axis, dtype=np.float64)
    n = float(np.linalg.norm(axis))
    if n < 1e-15:
        raise ValueError("Axis must be a non-zero vector")
    axis = axis / n
    half = angle / 2.0
    s = math.sin(half)
    return Quaternion(math.cos(half), axis[0] * s, axis[1] * s, axis[2] * s)


def from_components(arr: np.ndarray) -> Quaternion:
    """Construct from a length-4 NumPy array [w, x, y, z]."""
    arr = np.asarray(arr, dtype=np.float64)
    if arr.shape != (4,):
        raise ValueError("Array must have exactly 4 elements")
    return Quaternion(float(arr[0]), float(arr[1]), float(arr[2]), float(arr[3]))


# ---------------------------------------------------------------------------
# SLERP
# ---------------------------------------------------------------------------

def slerp(q1: Quaternion, q2: Quaternion, t: float) -> Quaternion:
    """Spherical linear interpolation between q1 (t=0) and q2 (t=1)."""
    if not (0.0 <= t <= 1.0):
        raise ValueError(f"t must be in [0, 1]; got {t}")
    dot = float(np.dot(q1._q, q2._q))
    # Shortest-path convention: negate q2 if dot < 0
    q2_arr = q2._q.copy()
    if dot < 0.0:
        q2_arr = -q2_arr
        dot = -dot
    dot = float(np.clip(dot, -1.0, 1.0))
    if dot > 0.9995:
        # Nearly identical — use normalised linear interpolation
        result = q1._q + t * (q2_arr - q1._q)
        return from_components(result).normalize()
    theta_0 = math.acos(dot)
    theta = theta_0 * t
    sin_theta = math.sin(theta)
    sin_theta_0 = math.sin(theta_0)
    s1 = math.cos(theta) - dot * sin_theta / sin_theta_0
    s2 = sin_theta / sin_theta_0
    return from_components(s1 * q1._q + s2 * q2_arr)


# ---------------------------------------------------------------------------
# CQHML manifold helpers
# ---------------------------------------------------------------------------

# Canonical inter-layer rotation axis (ontology dimension axis)
_LAYER_AXIS = np.array([0.0, 1.0, 0.0], dtype=np.float64)


def layer_rotation(source_layer: int, target_layer: int) -> Quaternion:
    """Return the canonical quaternion encoding an L-layer ontology transition.

    Rotation angle = (target − source) × π/20 radians.
    Identity (angle=0) when source == target.
    Layer range enforced: [1, 10] per 10-layer ontology stack.
    """
    if not (1 <= source_layer <= 10 and 1 <= target_layer <= 10):
        raise ValueError(f"Layers must be in [1, 10]; got {source_layer}, {target_layer}")
    angle = (target_layer - source_layer) * math.pi / 20.0
    return from_axis_angle(_LAYER_AXIS, angle)


def phi_coherent(q: Quaternion, tol: float = 1e-9) -> bool:
    """G₂ 3-form coherence check.

    A quaternion is G₂-coherent iff it is a unit quaternion in the positive
    hemisphere (w ≥ 0). This mirrors the phi_parallel flag in DimensionalCoordinate.
    """
    return bool(abs(q.norm() - 1.0) < tol and q.w >= 0.0)


def ensure_positive_hemisphere(q: Quaternion) -> Quaternion:
    """Canonicalise a unit quaternion to the positive hemisphere (w ≥ 0)."""
    q = q.normalize()
    if q.w < 0.0:
        return -q
    return q


def compose_layer_path(layers: list[int]) -> Quaternion:
    """Compose quaternion rotations along a sequence of layer indices.

    compose_layer_path([L1, L2, L3]) = layer_rotation(L1, L2) * layer_rotation(L2, L3)
    """
    if len(layers) < 2:
        raise ValueError("Need at least 2 layers to compose a path")
    result = layer_rotation(layers[0], layers[1])
    for i in range(2, len(layers)):
        result = result * layer_rotation(layers[i - 1], layers[i])
    return result
