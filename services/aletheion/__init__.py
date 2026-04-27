"""Aletheion v2.0 — Logos/Canon/PreAction gate service."""
__version__ = "2.0"

from .logos_gate import logos_gate, LogosConstraintCheck
from .canon_readiness import assess_canon_readiness, CanonReadinessRequest
from .pre_action import pre_action_check
