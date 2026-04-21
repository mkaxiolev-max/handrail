"""Autonomy tiers — AXIOLEV Holdings LLC © 2026.
Per Ω-Logos spec. Each tier expands the action surface but retains PDP gate."""
from enum import IntEnum

class Tier(IntEnum):
    OBSERVE_ONLY         = 0
    PROPOSE_ONLY         = 1
    REVERSIBLE_EXECUTION = 2
    BOUNDED_WORKFLOWS    = 3
    LONG_HORIZON         = 4
    STRATEGIC            = 5

# Default ceiling for production safety
DEFAULT_CEILING = Tier.BOUNDED_WORKFLOWS

def gate(requested: Tier, ceiling: Tier = DEFAULT_CEILING) -> Tier:
    """Clamp requested tier to ceiling — bounded omnipotence / kenosis."""
    return Tier(min(int(requested), int(ceiling)))
