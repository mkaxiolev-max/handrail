# Copyright © 2026 AXIOLEV Holdings LLC. All rights reserved.
"""
NS-AL VerificationDispatcher.

Given a ComputationContract + artifact bundle, dispatches to the appropriate
verifier and produces either a VerificationReceipt or an ObligationArtifact.

Invariant 11 enforcement matrix:
  no justification artifacts  → ObligationArtifact (PENDING)
  resolved obligation present → VerificationReceipt (VERIFIED)
  receipt without justification → VerificationReceipt (REJECTED)
  failed proof/cert/claim    → VerificationReceipt (REJECTED)
  R4 + !yubikey_verified     → VerificationReceipt (REJECTED)
  all checks pass            → VerificationReceipt (VERIFIED)
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from .types import (
    BoundedClaim,
    CertificateArtifact,
    ComputationContract,
    ObligationArtifact,
    ObligationStatus,
    ProofArtifact,
    RiskTier,
    Verdict,
    VerificationReceipt,
)

YUBIKEY_SERIAL_PRIMARY = "26116460"

_LOG_SSD      = Path("/Volumes/NSExternal/ALEXANDRIA/ledger/assurance_receipts.jsonl")
_LOG_FALLBACK = Path.home() / "ALEXANDRIA" / "ledger" / "assurance_receipts.jsonl"


def _log_path() -> Path:
    if Path("/Volumes/NSExternal/ALEXANDRIA/ledger").exists():
        return _LOG_SSD
    p = _LOG_FALLBACK
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _deadline_iso(hours: int = 72) -> str:
    dt = datetime.now(timezone.utc) + timedelta(hours=hours)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_dict(d: dict) -> str:
    raw = json.dumps(d, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(raw.encode()).hexdigest()


def _bundle_hash(contract: ComputationContract, artifacts: list, prev_hash: Optional[str]) -> str:
    return _sha256_dict({
        "risk_tier":      contract.risk_tier.value,
        "artifact_count": len(artifacts),
        "artifact_types": sorted(type(a).__name__ for a in artifacts),
        "prev_hash":      prev_hash or ("0" * 64),
    })


def _append_log(entry: dict) -> None:
    try:
        with open(_log_path(), "a") as fh:
            fh.write(json.dumps(entry) + "\n")
    except OSError:
        pass


class VerificationDispatcher:
    """
    Stateless dispatcher.  Call dispatch() per transition attempt.
    Use dispatch(..., prev_hash=receipt.subject_hash) to build a receipt chain.
    """

    def dispatch(
        self,
        contract:         ComputationContract,
        artifacts:        list[Any],
        yubikey_verified: bool = False,
        prev_hash:        Optional[str] = None,
    ) -> tuple[Optional[VerificationReceipt], Optional[ObligationArtifact]]:
        ts = _now_iso()
        bh = _bundle_hash(contract, artifacts, prev_hash)

        proofs       = [a for a in artifacts if isinstance(a, ProofArtifact)]
        certs        = [a for a in artifacts if isinstance(a, CertificateArtifact)]
        claims       = [a for a in artifacts if isinstance(a, BoundedClaim)]
        obligations  = [a for a in artifacts if isinstance(a, ObligationArtifact)]
        ext_receipts = [a for a in artifacts if isinstance(a, VerificationReceipt)]

        justifications = proofs + certs + claims

        # I11-b: VerificationReceipt submitted without any backing justification → reject
        if ext_receipts and not justifications:
            receipt = VerificationReceipt(
                subject_hash=bh,
                verdict=Verdict.REJECTED,
                evidence_refs=["err:no_justification_for_receipt"],
                timestamp=ts,
            )
            _append_log({"event": "rejected_no_justification", "ts": ts})
            return receipt, None

        # I11-c: No justification artifacts present
        if not justifications:
            resolved = [o for o in obligations if o.status == ObligationStatus.RESOLVED]
            if resolved:
                ob = resolved[0]
                receipt = VerificationReceipt(
                    subject_hash=bh,
                    verdict=Verdict.VERIFIED,
                    evidence_refs=[
                        f"obligation_resolved:{ob.compensating_action}",
                        *(([f"prev:{prev_hash}"] if prev_hash else [])),
                    ],
                    timestamp=ts,
                )
                _append_log({"event": "obligation_resolved", "ts": ts})
                return receipt, None

            # No justification, no resolved obligation → emit pending obligation
            ob = obligations[0] if obligations else ObligationArtifact(
                owner=str(contract.inputs_schema.get("owner", "system")),
                deadline=_deadline_iso(),
                compensating_action="provide_justification_artifact",
                status=ObligationStatus.PENDING,
            )
            _append_log({"event": "obligation_pending", "ts": ts})
            return None, ob

        # Have justification artifacts → verify each
        evidence_refs: list[str] = []

        for proof in proofs:
            ok, reason, ref = self._verify_proof(proof)
            if not ok:
                receipt = VerificationReceipt(
                    subject_hash=bh,
                    verdict=Verdict.REJECTED,
                    evidence_refs=[f"err:{reason}"],
                    timestamp=ts,
                )
                _append_log({"event": "proof_rejected", "reason": reason, "ts": ts})
                return receipt, None
            evidence_refs.append(ref)

        for cert in certs:
            ok, reason, ref = self._verify_cert(cert)
            if not ok:
                receipt = VerificationReceipt(
                    subject_hash=bh,
                    verdict=Verdict.REJECTED,
                    evidence_refs=[f"err:{reason}"],
                    timestamp=ts,
                )
                _append_log({"event": "cert_rejected", "reason": reason, "ts": ts})
                return receipt, None
            evidence_refs.append(ref)

        for claim in claims:
            ok, reason, ref = self._verify_claim(claim)
            if not ok:
                receipt = VerificationReceipt(
                    subject_hash=bh,
                    verdict=Verdict.REJECTED,
                    evidence_refs=[f"err:{reason}"],
                    timestamp=ts,
                )
                _append_log({"event": "claim_rejected", "reason": reason, "ts": ts})
                return receipt, None
            evidence_refs.append(ref)

        # R4 gate — YubiKey 26116460 must be pre-verified upstream
        if contract.risk_tier == RiskTier.R4 and not yubikey_verified:
            receipt = VerificationReceipt(
                subject_hash=bh,
                verdict=Verdict.REJECTED,
                evidence_refs=["err:r4_requires_yubikey_26116460"],
                timestamp=ts,
            )
            _append_log({"event": "r4_yubikey_gate_fail", "ts": ts})
            return receipt, None

        if prev_hash:
            evidence_refs.append(f"prev:{prev_hash}")

        receipt = VerificationReceipt(
            subject_hash=bh,
            verdict=Verdict.VERIFIED,
            evidence_refs=evidence_refs,
            timestamp=ts,
        )
        _append_log({"event": "verified", "evidence_count": len(evidence_refs), "ts": ts})
        return receipt, None

    # ------------------------------------------------------------------
    # Per-type verifiers
    # ------------------------------------------------------------------

    def _verify_proof(self, proof: ProofArtifact) -> tuple[bool, str, str]:
        from .types import make_proof_hash
        expected = make_proof_hash(proof.content)
        if proof.hash != expected:
            return False, "proof_hash_mismatch", ""
        ref = f"proof:{proof.kind.value}:{proof.hash[7:23]}"
        return True, "", ref

    def _verify_cert(self, cert: CertificateArtifact) -> tuple[bool, str, str]:
        try:
            expiry = datetime.fromisoformat(cert.expiry.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return False, "cert_invalid_expiry_format", ""
        if expiry <= datetime.now(timezone.utc):
            return False, "cert_expired", ""
        ref = f"cert:{cert.subject}:{cert.issuer}"
        return True, "", ref

    def _verify_claim(self, claim: BoundedClaim) -> tuple[bool, str, str]:
        if not (0.0 <= claim.confidence <= 1.0):
            return False, "claim_confidence_out_of_range", ""
        ref = f"claim:{claim.predicate[:32]}:{claim.confidence:.3f}"
        return True, "", ref


# ---------------------------------------------------------------------------
# Receipt chain utilities
# ---------------------------------------------------------------------------

def verify_receipt_chain(receipts: list[VerificationReceipt]) -> bool:
    """
    Verify that each receipt (after the first) references its predecessor's
    subject_hash via a 'prev:<hash>' entry in evidence_refs.
    """
    for i in range(1, len(receipts)):
        expected_ref = f"prev:{receipts[i - 1].subject_hash}"
        if not any(ref == expected_ref for ref in receipts[i].evidence_refs):
            return False
    return True
