"""Role definitions."""
from enum import Enum


class Role(str, Enum):
    FOUNDER = "founder"
    OPERATOR = "operator"
    OBSERVER = "observer"
    SYSTEM = "system"


FOUNDER_POLICY_PROFILE = "founder"
