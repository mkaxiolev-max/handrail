"""Shared fixtures — AXIOLEV Holdings LLC © 2026."""
import pytest
from services.omega_logos.runtime.core import Orchestrator
from services.omega_logos.runtime.autonomy import Tier

@pytest.fixture
def orch():
    return Orchestrator(tier=Tier.BOUNDED_WORKFLOWS)
