from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List
from pathlib import Path

@dataclass
class ComponentSpec:
    name: str; kind: str; props: Dict[str,str]; description: str

CANONICAL = {
    "GovernorZoneIndicator": ComponentSpec("GovernorZoneIndicator","widget",
        {"zone":"string","score":"number","delta":"number?"},"Live governor zone display"),
    "ReceiptChainVisualizer": ComponentSpec("ReceiptChainVisualizer","visualizer",
        {"receipts":"Receipt[]","maxVisible":"number"},"Merkle receipt chain visualization"),
    "HormeticProfileWidget": ComponentSpec("HormeticProfileWidget","widget",
        {"profile":"BandScores","signature":"Signature"},"B0-B5 profile line chart"),
    "CalibrationReliabilityDiagram": ComponentSpec("CalibrationReliabilityDiagram","visualizer",
        {"bins":"CalibrationBin[]","ece":"number","mce":"number"},"Reliability diagram"),
    "I1ScorePanel": ComponentSpec("I1ScorePanel","panel",{"score":"number","domains":"DomainBreakdown[]"},"I₁ composite"),
    "I2HelmMatrix": ComponentSpec("I2HelmMatrix","visualizer",{"matrix":"number[][]"},"9×5 HELM heatmap"),
    "I3UoieComposite": ComponentSpec("I3UoieComposite","panel",{"metrics":"UoieMetrics"},"I₃ UOIE v2"),
    "I4GpxOmega": ComponentSpec("I4GpxOmega","panel",{"metrics":"GpxMetrics"},"I₄ GPX-Ω"),
    "I5SaqPanel": ComponentSpec("I5SaqPanel","panel",{"axes":"SaqAxes"},"I₅ SAQ"),
    "MasterCompositeGauge": ComponentSpec("MasterCompositeGauge","gauge",{"score":"number","tier":"string"},"Master gauge"),
}

TOKENS = """:root {
  --axiolev-black:#0A0A0A; --axiolev-ink:#1A1A1A; --axiolev-gold:#C9A961;
  --axiolev-gold-dark:#8A7340; --axiolev-gray:#4A4A4A; --axiolev-light:#F5F2EB;
  --zone-block:#7A1F1F; --zone-review:#8A7340; --zone-pass:#2D4A2D; --zone-high-assurance:#C9A961;
}"""

class UIRegenerator:
    def __init__(self, ui_root: str): self.ui_root=Path(ui_root)

    def regenerate_all(self) -> List[str]:
        created=[]
        d=self.ui_root/"components"/"axiolev"; d.mkdir(parents=True,exist_ok=True)
        for name,spec in CANONICAL.items():
            f=d/f"{name}.tsx"
            if not f.exists():
                props="\n".join(f"  {k}:{v};" for k,v in spec.props.items())
                f.write_text(f"// {name} — {spec.description}\nimport React from 'react';\nexport interface {name}Props {{\n{props}\n}}\nexport const {name}: React.FC<{name}Props> = (props) => <div className='axiolev-{spec.kind}'/>;\nexport default {name};\n")
                created.append(str(f))
        t=self.ui_root/"styles"; t.mkdir(parents=True,exist_ok=True)
        tf=t/"axiolev-tokens.css"
        if not tf.exists(): tf.write_text(TOKENS); created.append(str(tf))
        return created
