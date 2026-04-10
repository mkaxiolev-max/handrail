"""
Omega policy guards — HIC/PDP enforcement at Omega route boundary.
Every simulate and compare-to-reality path must pass through these guards.
Omega is a simulation-to-action bridge: highest-risk surface in the system.
"""
from .guards import (
    omega_hic_guard,
    omega_pdp_guard,
    OmegaPolicyError,
    build_policy_state,
    ADVISORY_ONLY,
    VETOED,
    DENIED,
    FOUNDER_AUTHORIZED,
)
