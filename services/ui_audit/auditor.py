from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict
from pathlib import Path
import re

class Severity(str, Enum):
    INFO="INFO"; WARN="WARN"; VIOLATION="VIOLATION"; BLOCKER="BLOCKER"

@dataclass
class AuditFinding:
    component: str; severity: Severity; spec_requirement: str
    actual: str; recommendation: str

VIOLET_PALETTE={"black":"#0A0A0A","ink":"#1A1A1A","gold":"#C9A961","gold_dark":"#8A7340","gray":"#4A4A4A","light":"#F5F2EB"}
REQUIRED_COMPONENTS=["GovernorZoneIndicator","ReceiptChainVisualizer","HormeticProfileWidget",
    "CalibrationReliabilityDiagram","I1ScorePanel","I2HelmMatrix","I3UoieComposite",
    "I4GpxOmega","I5SaqPanel","MasterCompositeGauge"]

class UIAuditor:
    def __init__(self, ui_root: str): self.ui_root=Path(ui_root)

    def audit(self) -> List[AuditFinding]:
        findings=[]
        if not self.ui_root.exists():
            return [AuditFinding("ui_root",Severity.BLOCKER,"UI root must exist",
                                 f"{self.ui_root} not found","Create UI root")]
        findings.extend(self._audit_components())
        findings.extend(self._audit_voice())
        return findings

    def _audit_components(self):
        existing={p.stem for p in self.ui_root.rglob("*.*")}
        return [AuditFinding(f"component.{c}",Severity.VIOLATION,f"Violet requires {c}",
                             "not found",f"Generate {c} stub")
                for c in REQUIRED_COMPONENTS if c not in existing]

    def _audit_voice(self):
        found=any(re.search(r'(voice|speech|twilio|polly)',p.read_text(errors="ignore"),re.I)
                  for p in list(self.ui_root.rglob("*.*"))[:200] if p.is_file())
        if not found:
            return [AuditFinding("voice_primitive",Severity.VIOLATION,
                                 "Violet requires voice-first","no voice refs found",
                                 "Install voice gateway")]
        return []
