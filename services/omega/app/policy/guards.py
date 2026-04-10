"""
Omega policy guards — explicit HIC/PDP rails for Omega routes.

CONTRACT:
  - /omega/simulate: advisory_only by default.
    - If allow_promotion or allow_execution is True → HIC evaluate → VETO = 403.
    - Always adds policy_state and promotion_allowed to response.
  - /omega/runs/{id}/compare: PDP gate on any status-altering path.
    - If compare can update promotion readiness → PDP decide → DENY = 403.
    - Always adds policy_state to response.

Design rule: fail closed.
If policy engine is unavailable, default is DENY, not allow.
"""
from __future__ import annotations
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger("omega.policy")

ADVISORY_ONLY = "advisory_only"
VETOED = "vetoed"
DENIED = "denied"
FOUNDER_AUTHORIZED = "founder_authorized"

NS_CORE_URL = "http://ns_core:9000"


class OmegaPolicyError(Exception):
    def __init__(self, verdict: str, reason: str):
        self.verdict = verdict
        self.reason = reason
        super().__init__(f"Omega policy {verdict}: {reason}")


def _hic_evaluate(text: str) -> str:
    """
    Call ns_core /hic/evaluate. Returns verdict string.
    Fails closed: if unavailable, returns VETO.
    """
    try:
        payload = json.dumps({"text": text}).encode()
        req = urllib.request.Request(
            f"{NS_CORE_URL}/hic/evaluate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=4) as r:
            data = json.loads(r.read())
            return data.get("verdict", "VETO").upper()
    except Exception as e:
        logger.warning("HIC unavailable: %s — failing closed with VETO", e)
        return "VETO"


def _pdp_decide(subject: str, action: str, resource: str) -> str:
    """
    Call ns_core /pdp/decide. Returns effect string.
    Fails closed: if unavailable, returns DENY.
    """
    try:
        payload = json.dumps({"subject": subject, "action": action, "resource": resource}).encode()
        req = urllib.request.Request(
            f"{NS_CORE_URL}/pdp/decide",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=4) as r:
            data = json.loads(r.read())
            return data.get("effect", "DENY").upper()
    except Exception as e:
        logger.warning("PDP unavailable: %s — failing closed with DENY", e)
        return "DENY"


def omega_hic_guard(
    intent: str,
    allow_promotion: bool = False,
    allow_execution: bool = False,
    operator: str = "founder",
) -> str:
    """
    HIC guard for /omega/simulate.

    Returns policy_state string.
    Raises OmegaPolicyError(VETOED) if promotion/execution requested and HIC says VETO.
    Default path (advisory only) requires no HIC check.
    """
    if not allow_promotion and not allow_execution:
        return ADVISORY_ONLY

    verdict = _hic_evaluate(f"{intent} promote execute")
    if verdict == "VETO":
        raise OmegaPolicyError(
            VETOED,
            f"HIC vetoed promotion/execution request. Intent: '{intent[:60]}'. "
            "Omega simulation is advisory-only until founder explicitly authorizes.",
        )
    if verdict in ("R0", "R1"):
        return FOUNDER_AUTHORIZED
    raise OmegaPolicyError(VETOED, f"HIC returned unknown verdict '{verdict}' — failing closed")


def omega_pdp_guard(
    operator: str,
    run_id: str,
    can_alter_status: bool = True,
) -> str:
    """
    PDP guard for /omega/runs/{id}/compare.

    Returns policy_state string.
    Raises OmegaPolicyError(DENIED) if PDP denies the compare operation.
    """
    if not can_alter_status:
        return ADVISORY_ONLY

    effect = _pdp_decide(
        subject=f"operator:{operator}",
        action="omega_compare",
        resource="omega:run",
    )
    if effect == "DENY":
        raise OmegaPolicyError(
            DENIED,
            f"PDP denied compare-to-reality for operator '{operator}' on run '{run_id}'.",
        )
    return ADVISORY_ONLY


def build_policy_state(
    policy_state: str,
    promotion_allowed: bool = False,
    receipt_hash: str = "",
) -> dict:
    """Standard Omega policy envelope — every Omega response carries this."""
    return {
        "policy_state": policy_state,
        "promotion_allowed": promotion_allowed,
        "execution_allowed": False,
        "receipt_hash": receipt_hash,
        "constitution": "NS∞ — Omega is advisory unless founder-authorized",
    }
