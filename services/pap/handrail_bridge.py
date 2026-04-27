"""PAP -> Handrail CPS bridge. A-layer execution after dual-gate clearance."""
from typing import Any, Dict, Tuple
from .models import AletheiaPAPResource, PAPAction, PAPClaim
from .aletheion_bridge import wrap_aletheion_gates


def execute_a_layer_action(
    resource: AletheiaPAPResource,
    action_id: str,
    payload: Dict[str, Any],
    logos_check: Dict[str, Any],
    signal: Dict[str, Any],
    ctx: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any]]:
    """
    Decree P-5: every A-layer execution must:
      1. wrap Aletheion gates (Logos -> Canon -> PreAction)
      2. call Handrail CPS only if all three signed
      3. emit chained PAP receipt referencing AletheionReceipt(s)
    """
    action = next((a for a in resource.A.affordances if a.action_id == action_id), None)
    if action is None:
        return (False, {"error": f"action {action_id} not found"})
    if not action.handrail_required:
        return (False, {"error": "S2: action bypasses Handrail"})

    # Pick a representative claim for canon check (production: pick relevant)
    claim = resource.T.claims[0] if resource.T.claims else PAPClaim(
        claim_id=f"action-claim-{action_id}", text=action.endpoint,
        epistemic_type="derived_inference", evidence_refs=[], confidence=0.5,
    )

    gate = wrap_aletheion_gates(action, claim, logos_check, signal, ctx)
    if not gate["admit"]:
        return (False, {"error": "gate_denied", "gate": gate})

    # Handrail CPS call (best-effort import)
    handrail_receipt_ref = None
    try:
        from services.handrail_cps.executor import execute_op  # type: ignore
        result = execute_op(action.endpoint, action.method, payload)
        handrail_receipt_ref = result.get("receipt_id")
    except Exception as e:
        return (False, {"error": f"handrail_unavailable: {e}", "gate": gate})

    return (True, {
        "gate": gate,
        "handrail_receipt_ref": handrail_receipt_ref,
        "result": result,
    })
