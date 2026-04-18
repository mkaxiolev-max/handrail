"""NS∞ Oracle v2 contract schemas (C5).

Tag: oracle-v2-contract-v2
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict

from ns.api.schemas.common import IntegrityRouteEffect, RouteIntent


class OracleDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    ESCALATE = "ESCALATE"
    DEFER = "DEFER"


class OracleSeverity(str, Enum):
    NOMINAL = "NOMINAL"
    ADVISORY = "ADVISORY"
    CRITICAL = "CRITICAL"
    CONSTITUTIONAL = "CONSTITUTIONAL"


class HandrailScope(str, Enum):
    LOCAL = "LOCAL"
    DISTRIBUTED = "DISTRIBUTED"
    SOVEREIGN = "SOVEREIGN"


class ConstitutionalContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invariants_checked: list[str] = []
    never_events_screened: list[str] = []
    dignity_kernel_invoked: bool = False
    g2_phi_parallel: bool = True


class OracleCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    condition_id: str
    description: str
    satisfied: bool
    severity: OracleSeverity = OracleSeverity.ADVISORY


class OracleBlockingReason(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason_id: str
    description: str
    invariant_ref: Optional[str] = None
    severity: OracleSeverity = OracleSeverity.CRITICAL


class HandrailExecutionEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: HandrailScope = HandrailScope.LOCAL
    risk_tier: str = "R0"
    yubikey_verified: bool = False
    policy_profile: Optional[str] = None
    op_domain: Optional[str] = None
    op_name: Optional[str] = None


class OracleAdjudicationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    tick: int = 0
    envelope: HandrailExecutionEnvelope
    constitutional_context: ConstitutionalContext = ConstitutionalContext()
    ril_route_effect: IntegrityRouteEffect = IntegrityRouteEffect.PASS
    ril_aggregate_score: float = 1.0
    context: dict = {}


class OracleAdjudicationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    decision: OracleDecision
    severity: OracleSeverity
    conditions_checked: list[OracleCondition] = []
    blocking_reasons: list[OracleBlockingReason] = []
    route_intent: RouteIntent
    receipts_emitted: list[str] = []
    founder_translation: Optional[str] = None
    trace: list[str] = []
    tick: int = 0
