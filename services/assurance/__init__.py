# Copyright © 2026 AXIOLEV Holdings LLC. All rights reserved.
"""
services.assurance — NS-AL AssuranceLayer

Proof-carrying execution enforcement for Constitutional Invariant 11:
  "No state transition without a receipt.
   No receipt without a justification artifact.
   No artifact without verification or obligation."

I7 Certification Power Score credit: +8.0
"""
from .types import (
    BoundedClaim,
    CertificateArtifact,
    ComputationContract,
    ObligationArtifact,
    ObligationStatus,
    ProofArtifact,
    ProofKind,
    RiskTier,
    Verdict,
    VerificationReceipt,
    make_proof_hash,
)
from .dispatcher import VerificationDispatcher, verify_receipt_chain
from .enforcement import AssuranceViolation, assured

__version__ = "1.0.0"

__all__ = [
    # types
    "ComputationContract",
    "ProofArtifact",
    "CertificateArtifact",
    "BoundedClaim",
    "ObligationArtifact",
    "VerificationReceipt",
    "RiskTier",
    "ProofKind",
    "ObligationStatus",
    "Verdict",
    "make_proof_hash",
    # dispatcher
    "VerificationDispatcher",
    "verify_receipt_chain",
    # enforcement
    "assured",
    "AssuranceViolation",
]
