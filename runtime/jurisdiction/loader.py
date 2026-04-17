"""
AXIOLEV NS∞ — JurisdictionBundle

Adds a jurisdiction-layered policy to the existing PolicyBundle pattern.
Additive only: can tighten, never loosen, the gates established above it.

Precedence:  DK > Canon > PolicyBundle > JurisdictionBundle > RoleBinding
Owner:       AXIOLEV Holdings LLC. No LLM legal claim.
"""
import json
from pathlib import Path

JURISDICTION_ROOT = Path("policies/jurisdictions")


class JurisdictionBundle:
    def __init__(self, jurisdiction, vertical, spec):
        self.jurisdiction = jurisdiction
        self.vertical = vertical
        self.spec = spec

    @property
    def gates(self):
        return self.spec.get("rules", {}) or self.spec.get("gates", {})

    @property
    def forbidden_actions(self):
        return self.spec.get("forbidden_actions", [])

    @property
    def required_receipts(self):
        return self.spec.get("required_receipts", [])

    @property
    def citations(self):
        return self.spec.get("citations", [])

    def enforces(self, gate_name):
        return bool(self.gates.get(gate_name, False))

    def to_dict(self):
        return {
            "jurisdiction": self.jurisdiction,
            "vertical": self.vertical,
            "gates": self.gates,
            "forbidden_actions": self.forbidden_actions,
            "required_receipts": self.required_receipts,
            "citations": self.citations,
        }


def load_jurisdiction(jurisdiction, vertical="brokerage"):
    code = jurisdiction.lower()
    path = JURISDICTION_ROOT / code / f"{vertical}.json"
    if not path.exists():
        raise FileNotFoundError(f"No jurisdiction pack for ({jurisdiction},{vertical}) at {path}")
    spec = json.loads(path.read_text())
    return JurisdictionBundle(jurisdiction=code.upper(), vertical=vertical, spec=spec)


def list_available():
    out = []
    if not JURISDICTION_ROOT.exists():
        return out
    for jdir in JURISDICTION_ROOT.iterdir():
        if jdir.is_dir():
            for f in jdir.glob("*.json"):
                out.append((jdir.name.upper(), f.stem))
    return sorted(out)
