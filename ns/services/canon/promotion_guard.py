"""Canon promotion guard — Ring 4 six-condition gate (I1 + I4 + Ring 6) + NCOM/PIIC gate (B4)."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from ns.domain.models.g2_invariant import ring6_phi_parallel
from ns.domain.receipts.emitter import ReceiptEmitter
from ns.services.loom.service import ConfidenceEnvelope
from ns.services.ncom.state import NCOMState, COLLAPSE_READY_STATES
from ns.services.piic.chain import PIICStage


def verify_hardware_quorum(quorum_certs: list[dict]) -> bool:
    """Byzantine ≥2f+1 quorum with YubiKey 26116460 as mandatory singleton signer (I4/I9)."""
    yubi_present = any(c.get("serial") == "26116460" for c in quorum_certs)
    f = (len(quorum_certs) - 1) // 3
    return yubi_present and len(quorum_certs) >= 2 * f + 1


def _ncom_piic_gate(context: dict) -> tuple[bool, Optional[str]]:
    """Check NCOM/PIIC collapse gate (B4).

    Returns (passed, veto_reason).  veto_reason is None when passed.
    """
    # NCOM state must be in {ready_for_collapse, forced_collapse}
    ncom_state = context.get("ncom_state")
    if ncom_state is not None:
        if isinstance(ncom_state, str):
            try:
                ncom_state = NCOMState(ncom_state)
            except ValueError:
                return False, f"unknown_ncom_state:{ncom_state}"
        if ncom_state not in COLLAPSE_READY_STATES:
            return False, f"ncom_state_not_collapse_ready:{ncom_state.value}"

    # PIIC stage must be commitment
    piic_stage = context.get("piic_stage")
    if piic_stage is not None:
        if isinstance(piic_stage, str):
            try:
                piic_stage = PIICStage(piic_stage)
            except ValueError:
                return False, f"unknown_piic_stage:{piic_stage}"
        if piic_stage != PIICStage.commitment:
            return False, f"piic_stage_not_commitment:{piic_stage.value}"

    # readiness.recommendedAction must be "collapse" and hardVetoes must be empty
    readiness = context.get("readiness")
    if readiness is not None:
        if readiness.recommendedAction != "collapse":
            return False, f"readiness_action_not_collapse:{readiness.recommendedAction}"
        if readiness.hardVetoes:
            return False, f"hard_vetoes_present:{readiness.hardVetoes}"

    return True, None


class PromotionGuard:
    """Six-condition canon promotion gate + NCOM/PIIC gate.

    Conditions (all must pass):
    1. confidence.score() >= 0.82
    2. contradiction_weight <= 0.25
    3. reconstructability >= 0.90
    4. lineage_valid == True
    5. hic_approval == True
    6. pdp_approval == True
    Plus: hardware quorum (I4), ring6_phi_parallel (Ring 6 G₂ invariant).
    Plus (when present): NCOM/PIIC collapse gate (B4).
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
        passed, _ = _ncom_piic_gate(context)
        if not passed:
            return False
        return True

    def promote(
        self,
        branch_id: str,
        context: dict,
        receipt_path: Optional[Path] = None,
    ) -> dict:
        """Run the gate and emit a Lineage Fabric receipt.

        Returns a dict with keys: allowed, receipt_name, receipt_id, branch_id,
        and optionally veto_reason.
        """
        # Check NCOM/PIIC gate separately to emit ncom_veto_emitted receipt
        ncom_passed, veto_reason = _ncom_piic_gate(context)
        allowed = self.can_promote(branch_id, context)
        if not ncom_passed and veto_reason is not None:
            receipt_name = "ncom_veto_emitted"
        elif allowed:
            receipt_name = "canon_promoted_with_hardware_quorum"
        else:
            receipt_name = "canon_promotion_denied_i9_quorum_missing"
        receipt_id: Optional[str] = None
        if receipt_path is not None:
            emitter = ReceiptEmitter(receipt_path)
            receipt_id = emitter.append(receipt_name, {"branch_id": branch_id})
        result: dict = {
            "allowed": allowed,
            "receipt_name": receipt_name,
            "receipt_id": receipt_id,
            "branch_id": branch_id,
        }
        if veto_reason is not None:
            result["veto_reason"] = veto_reason
        return result
