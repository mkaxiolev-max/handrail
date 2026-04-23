# Copyright © 2026 AXIOLEV Holdings LLC. All rights reserved.
"""
NS-AL AssuranceLayer — domain types.

Constitutional Invariant 11:
  "No state transition without a receipt.
   No receipt without a justification artifact.
   No artifact without verification or obligation."
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class RiskTier(str, Enum):
    R0 = "R0"
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"
    R4 = "R4"


class ProofKind(str, Enum):
    FORMAL = "formal"
    EMPIRICAL = "empirical"
    ATTESTATION = "attestation"
    AUDIT = "audit"


class ObligationStatus(str, Enum):
    PENDING      = "pending"
    RESOLVED     = "resolved"
    OVERDUE      = "overdue"
    COMPENSATED  = "compensated"


class Verdict(str, Enum):
    VERIFIED           = "verified"
    REJECTED           = "rejected"
    OBLIGATION_PENDING = "obligation_pending"


@dataclass
class ComputationContract:
    """Formal specification of a state transition: what it accepts, produces, and promises."""
    inputs_schema:   Dict[str, Any]
    outputs_schema:  Dict[str, Any]
    preconditions:   List[Any]   # str labels or callables(inputs) -> bool
    postconditions:  List[Any]   # str labels or callables(result) -> bool
    side_effects:    List[str]
    risk_tier:       RiskTier


@dataclass
class ProofArtifact:
    """A verifiable proof object. hash must equal sha256(canonical JSON of content)."""
    kind:     ProofKind
    content:  Dict[str, Any]
    verifier: str
    hash:     str            # "sha256:<hex>" — computed via make_proof_hash()


@dataclass
class CertificateArtifact:
    """A signed certificate asserting claims about a subject, with an expiry."""
    subject:   str
    claims:    Dict[str, Any]
    issuer:    str
    signature: str
    expiry:    str           # ISO 8601 UTC e.g. "2026-12-31T00:00:00Z"


@dataclass
class BoundedClaim:
    """A probabilistic claim with a confidence bound and derivation lineage."""
    predicate:        str
    bound:            float
    confidence:       float  # in [0.0, 1.0]
    derivation_chain: List[str]


@dataclass
class ObligationArtifact:
    """A commitment to provide a justification artifact by a deadline."""
    owner:               str
    deadline:            str             # ISO 8601 UTC
    compensating_action: str
    status:              ObligationStatus


@dataclass
class VerificationReceipt:
    """Immutable record of a dispatch outcome. subject_hash covers contract + artifacts."""
    subject_hash:  str
    verdict:       Verdict
    evidence_refs: List[str]
    timestamp:     str          # ISO 8601 UTC


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def make_proof_hash(content: Dict[str, Any]) -> str:
    """Canonical sha256 hash for a ProofArtifact.content dict."""
    raw = json.dumps(content, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(raw.encode()).hexdigest()
