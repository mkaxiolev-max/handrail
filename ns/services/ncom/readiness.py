"""NCOM CollapseReadiness — evidence/contextual/interpretive gauges + vetoes (B2)."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CollapseReadiness:
    """Composite readiness signal for NCOM collapse gate.

    Fields
    ------
    ERS  — Evidence Readiness Score [0.0, 1.0]
    CRS  — Contextual Readiness Score [0.0, 1.0]
    IPI  — Interpretive Pressure Index [0.0, 1.0]
    contradictionPressure — current contradiction load [0.0, 1.0]; lower is better
    branchDiversityAdequacy — branch coverage score [0.0, 1.0]
    hardVetoes — list of veto reason strings; any entry blocks collapse
    """

    ERS: float = 0.0
    CRS: float = 0.0
    IPI: float = 0.0
    contradictionPressure: float = 0.0
    branchDiversityAdequacy: float = 0.0
    hardVetoes: list[str] = field(default_factory=list)

    @property
    def recommendedAction(self) -> str:
        """Derive action: 'veto' | 'collapse' | 'wait'."""
        if self.hardVetoes:
            return "veto"
        collapse_ready = (
            self.ERS >= 0.7
            and self.CRS >= 0.7
            and self.IPI >= 0.5
            and self.contradictionPressure <= 0.3
            and self.branchDiversityAdequacy >= 0.6
        )
        return "collapse" if collapse_ready else "wait"
