"""Governance router — /api/v1/governance/*"""
from fastapi import APIRouter
from shared.models.enums import SystemTier
from shared.policy.governance import get_never_events
from shared.receipts.generator import get_generator
from shared.models.enums import ReceiptType, RiskTier

router = APIRouter(prefix="/api/v1/governance", tags=["governance"])


@router.get("/state")
async def get_governance_state():
    return {
        "tier": SystemTier.ACTIVE,
        "constitution_version": "v5",
        "never_event_count": 7,
        "policy_bundles_loaded": 4,
        "quorum_model": "1-of-1 active (expands to 2-of-3 when slot_2 provisioned)",
        "yubikey_serials": ["26116460"],
        "conciliar_quorum_satisfied": True,
        "founder_policy_profile": "founder",
    }


@router.get("/never-events")
async def get_never_events_list():
    return {"never_events": get_never_events(), "count": 7}


@router.post("/simulate-policy")
async def simulate_policy(payload: dict):
    gen = get_generator()
    receipt = gen.issue_receipt(
        receipt_type=ReceiptType.GOVERNANCE,
        payload=payload,
        op="gov.simulate_policy",
        risk_tier=RiskTier.R1,
    )
    return {
        "simulated": True,
        "receipt_id": receipt.receipt_id,
        "result": "policy_pass",
        "payload": payload,
    }
