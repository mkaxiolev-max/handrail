"""Canon promotion guard — Ring 4 six-condition gate (I1 + I4 + Ring 6)."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from ns.domain.models.g2_invariant import ring6_phi_parallel
from ns.domain.receipts.emitter import ReceiptEmitter
from ns.services.loom.service import ConfidenceEnvelope


def verify_hardware_quorum(quorum_certs: list[dict]) -> bool:
    """Byzantine ≥2f+1 quorum with YubiKey 26116460 as mandatory singleton signer (I4/I9)."""
    yubi_present = any(c.get("serial") == "26116460" for c in quorum_certs)
    f = (len(quorum_certs) - 1) // 3
    return yubi_present and len(quorum_certs) >= 2 * f + 1


class PromotionGuard:
    """Six-condition canon promotion gate.

    Conditions (all must pass):
    1. confidence.score() >= 0.82
    2. contradiction_weight <= 0.25
    3. reconstructability >= 0.90
    4. lineage_valid == True
    5. hic_approval == True
    6. pdp_approval == True
    Plus: hardware quorum (I4), ring6_phi_parallel (Ring 6 G₂ invariant).
    """

    def can_promote(self, branch_id: str, context: dict) -> bool:  # noqa: ARG002
        envelope: Optional[ConfidenceEnvelope] = context.get("confidence")
        if envelope is None or envelope.score() < 0.82:
            return False
        if context.get("contradiction_weight", 1.0) > 0.25:
            return False
        if context.get("reconstructability", 0.0) < 0.90:
            return False
        if not context.get("lineage_valid", False):
            return False
        if not context.get("hic_approval", False):
            return False
        if not context.get("pdp_approval", False):
            return False
        if not verify_hardware_quorum(context.get("quorum_certs", [])):
            return False
        if not ring6_phi_parallel(context.get("state")):
            return False
        return True

    def promote(
        self,
        branch_id: str,
        context: dict,
        receipt_path: Optional[Path] = None,
    ) -> dict:
        """Run the gate and emit a Lineage Fabric receipt.

        Returns a dict with keys: allowed, receipt_name, receipt_id, branch_id.
        """
        allowed = self.can_promote(branch_id, context)
        receipt_name = (
            "canon_promoted_with_hardware_quorum"
            if allowed
            else "canon_promotion_denied_i9_quorum_missing"
        )
        receipt_id: Optional[str] = None
        if receipt_path is not None:
            emitter = ReceiptEmitter(receipt_path)
            receipt_id = emitter.append(receipt_name, {"branch_id": branch_id})
        return {
            "allowed": allowed,
            "receipt_name": receipt_name,
            "receipt_id": receipt_id,
            "branch_id": branch_id,
        }
