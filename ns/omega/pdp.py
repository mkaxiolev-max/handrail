"""
axiolev-omega-pdp-v2
AXIOLEV Holdings LLC © 2026

Policy Decision Point. Default-deny on anonymous principals.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PDPDecision:
    principal: Optional[str]
    action: str
    resource: str
    allowed: bool
    reason: str


def evaluate(
    principal: Optional[str],
    action: str,
    resource: str,
    allow_rules: Optional[dict] = None,
) -> PDPDecision:
    if not principal:
        return PDPDecision(None, action, resource, False, "anonymous: default-deny")
    rules = allow_rules or {}
    allowed_actions = rules.get(principal, [])
    if action in allowed_actions or "*" in allowed_actions:
        return PDPDecision(principal, action, resource, True, "allow-listed")
    return PDPDecision(principal, action, resource, False, "not-allowed")
