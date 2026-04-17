"""SimulationBranch.v1 — ABI-frozen extension of models.SimulationBranch."""
from __future__ import annotations

from typing import Literal

from models.simulation_branch import SimulationBranch as _Base


class SimulationBranch(_Base):
    schema_version: Literal[1] = 1
    dignity_banner: Literal[
        "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED"
    ] = "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED"
