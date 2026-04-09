"""
PolicyDecisionPoint (PDP) — ABAC enforcement for NS∞.

5 policy rules, projection actor policy, founder-required action gate,
PII redaction obligations.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Literal
from enum import Enum


# ── Effect ────────────────────────────────────────────────────────────────────

class Effect(str, Enum):
    ALLOW = "ALLOW"
    DENY  = "DENY"


# ── Request / Decision / Obligation ──────────────────────────────────────────

@dataclass
class PDPRequest:
    subject: str          # Who is requesting (actor/role)
    action: str           # What action
    resource: str         # On what resource
    projection: Optional[str] = None   # Projection context if applicable
    context: dict = field(default_factory=dict)

@dataclass
class ABACDecision:
    rule_id: str
    effect: Effect
    reason: str

@dataclass
class PDPObligation:
    obligation_type: str  # e.g. "redact_pii", "log_receipt", "require_yubikey"
    detail: str

@dataclass
class PDPDecision:
    effect: Effect
    reason: str
    matched_rules: list[ABACDecision]
    obligations: list[PDPObligation]
    subject: str
    action: str
    resource: str


# ── Projection actor policy ───────────────────────────────────────────────────

PROJECTION_ACTOR_POLICY: dict[str, list[str]] = {
    # projection_name → list of allowed subject prefixes
    "storytime:user":       ["user:", "session:"],
    "storytime:audit":      ["founder:", "ns:arbiter", "ns:internal"],
    "storytime:developer":  ["founder:", "developer:"],
    "ns:internal":          ["ns:", "founder:"],
    "handrail:exec":        ["handrail:", "ns:"],
    "alexandria:ingest":    ["alexandria:", "ns:", "founder:"],
    "alexandria:retrieve":  ["alexandria:", "ns:", "founder:", "user:"],
    "adapter:task":         ["adapter:", "ns:"],
    "ns:arbiter":           ["ns:arbiter", "founder:"],
    "ns:evidence_role":     ["ns:evidence_role", "ns:arbiter", "founder:"],
    "ns:counter_role":      ["ns:counter_role", "ns:arbiter", "founder:"],
    "ns:narrative_role":    ["ns:narrative_role", "ns:arbiter", "founder:"],
}

# Actions that require founder identity
FOUNDER_REQUIRED_ACTIONS = {
    "canon.promote",
    "policy.override",
    "gov.record_decision",
    "gov.issue_constraint",
    "ma.close_transaction",
    "knowledge.promote_to_canon",
    "yubikey.verify",
    "kernel.dignity_override",
}

# Resources containing PII — any access triggers redact_pii obligation
PII_RESOURCES = {
    "contacts",
    "voice_sessions",
    "user_profile",
    "email_content",
    "sms_content",
}


# ── PDP ──────────────────────────────────────────────────────────────────────

class PolicyDecisionPoint:
    """
    5-rule ABAC policy engine for NS∞.

    Rule 1: Projection actor policy — subject must match projection's allowed actors
    Rule 2: Founder-required actions — only founder: subjects may execute
    Rule 3: Deny unknown projection — unknown projection name → deny
    Rule 4: PII obligation — accessing PII resource requires redact_pii obligation
    Rule 5: Default allow — if no deny rule fires, allow with log_receipt obligation
    """

    def decide(self, request: PDPRequest) -> PDPDecision:
        matched_rules: list[ABACDecision] = []
        obligations: list[PDPObligation] = []

        # Rule 1: Projection actor policy
        if request.projection:
            if request.projection not in PROJECTION_ACTOR_POLICY:
                abac = ABACDecision(
                    rule_id="R3",
                    effect=Effect.DENY,
                    reason=f"Unknown projection '{request.projection}'",
                )
                matched_rules.append(abac)
                return PDPDecision(
                    effect=Effect.DENY,
                    reason=abac.reason,
                    matched_rules=matched_rules,
                    obligations=obligations,
                    subject=request.subject,
                    action=request.action,
                    resource=request.resource,
                )
            allowed_prefixes = PROJECTION_ACTOR_POLICY[request.projection]
            subject_allowed = any(request.subject.startswith(p) for p in allowed_prefixes)
            abac = ABACDecision(
                rule_id="R1",
                effect=Effect.ALLOW if subject_allowed else Effect.DENY,
                reason=(
                    f"Subject '{request.subject}' matches projection '{request.projection}' actor policy"
                    if subject_allowed
                    else f"Subject '{request.subject}' not permitted for projection '{request.projection}'"
                ),
            )
            matched_rules.append(abac)
            if not subject_allowed:
                return PDPDecision(
                    effect=Effect.DENY,
                    reason=abac.reason,
                    matched_rules=matched_rules,
                    obligations=obligations,
                    subject=request.subject,
                    action=request.action,
                    resource=request.resource,
                )

        # Rule 2: Founder-required actions
        if request.action in FOUNDER_REQUIRED_ACTIONS:
            is_founder = request.subject.startswith("founder:")
            abac = ABACDecision(
                rule_id="R2",
                effect=Effect.ALLOW if is_founder else Effect.DENY,
                reason=(
                    f"Action '{request.action}' requires founder identity — verified"
                    if is_founder
                    else f"Action '{request.action}' requires founder identity — subject '{request.subject}' denied"
                ),
            )
            matched_rules.append(abac)
            if not is_founder:
                return PDPDecision(
                    effect=Effect.DENY,
                    reason=abac.reason,
                    matched_rules=matched_rules,
                    obligations=obligations,
                    subject=request.subject,
                    action=request.action,
                    resource=request.resource,
                )

        # Rule 4: PII obligation
        if request.resource in PII_RESOURCES:
            obligations.append(PDPObligation(
                obligation_type="redact_pii",
                detail=f"Resource '{request.resource}' contains PII — output must be redacted before returning to non-founder surface",
            ))

        # Rule 5: Default allow + log_receipt obligation
        obligations.append(PDPObligation(
            obligation_type="log_receipt",
            detail=f"Action '{request.action}' on '{request.resource}' by '{request.subject}' — receipt required",
        ))

        matched_rules.append(ABACDecision(
            rule_id="R5",
            effect=Effect.ALLOW,
            reason="Default allow — no deny rule triggered",
        ))

        return PDPDecision(
            effect=Effect.ALLOW,
            reason="Policy evaluation passed",
            matched_rules=matched_rules,
            obligations=obligations,
            subject=request.subject,
            action=request.action,
            resource=request.resource,
        )


_pdp = PolicyDecisionPoint()

def get_pdp() -> PolicyDecisionPoint:
    return _pdp
