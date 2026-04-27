"""Aletheia-PAP Ω v1.0 — Parity Access Protocol wrapping Aletheion v2.0.

Decrees P-1 .. P-7. Five PAP Negations. Programs invariants #14, #15, #16.
"""
__version__ = "1.0"

from .models import (
    EpistemicType,
    HumanSurface, AgentSurface, TruthSurface,
    PAPAction, PAPClaim, PAPEvidence, PAPIdentity,
    AletheiaPAPResource, PAPReceipt, PAPQECFailure, PAPScore, TriadicScore,
)
from .hashing import (
    canonical_json, sha256_hex, layer_hash,
    compute_merkle_root, verify_merkle_root,
)
from .validator import validate_pap_resource
from .scoring import score_pap_resource
from .qec import detect_qec_syndromes
from .canon_bridge import triadic_canon_check
