"""MITRE ATLAS v5.4 — AI/ML threat tactic coverage matrix."""
from __future__ import annotations
from dataclasses import dataclass, field

ATLAS_TACTICS: list[str] = [
    "reconnaissance", "resource-development", "initial-access", "ml-attack-staging",
    "execution", "persistence", "privilege-escalation", "defense-evasion",
    "credential-access", "discovery", "lateral-movement", "collection",
    "ml-model-access", "exfiltration", "impact",
]


@dataclass
class TacticCoverage:
    tactic: str
    mitigations: list[str] = field(default_factory=list)
    detections: list[str] = field(default_factory=list)
    covered: bool = False


class ATLASCoverageMatrix:
    def __init__(self):
        self._matrix: dict[str, TacticCoverage] = {
            t: TacticCoverage(t) for t in ATLAS_TACTICS
        }
        # Pre-populate NS∞ known mitigations
        self._populate_ns_mitigations()

    def _populate_ns_mitigations(self) -> None:
        known = {
            "reconnaissance":        ["rate_limiting", "auth_gateway"],
            "initial-access":        ["yubikey_quorum", "auth_bypass_prevention"],
            "ml-attack-staging":     ["adversarial_test_suite", "dignity_kernel"],
            "execution":             ["cps_policy_gate", "risk_tier_gate"],
            "persistence":           ["append_only_ledger", "receipt_chain"],
            "defense-evasion":       ["gitleaks_scan", "transparency_log"],
            "ml-model-access":       ["veil_gate", "model_router"],
            "impact":                ["never_event_enforcement", "dignity_kernel"],
            "discovery":             ["capability_graph", "permission_model"],
            "exfiltration":          ["dignity_kernel_secrets_strip"],
        }
        for tactic, mitigations in known.items():
            if tactic in self._matrix:
                self._matrix[tactic].mitigations = mitigations
                self._matrix[tactic].covered = True

    def add_mitigation(self, tactic: str, mitigation: str) -> None:
        if tactic not in self._matrix:
            raise ValueError(f"Unknown tactic: {tactic}")
        self._matrix[tactic].mitigations.append(mitigation)
        self._matrix[tactic].covered = True

    def coverage_pct(self) -> float:
        covered = sum(1 for t in self._matrix.values() if t.covered)
        return round(covered / len(self._matrix) * 100, 1)

    def uncovered_tactics(self) -> list[str]:
        return [t for t, c in self._matrix.items() if not c.covered]

    def tactic_count(self) -> int:
        return len(ATLAS_TACTICS)
