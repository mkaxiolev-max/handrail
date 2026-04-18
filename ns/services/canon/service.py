"""L1 Constitutional Layer — Canon service stub (Ring 1)."""
from __future__ import annotations

from typing import Dict, List

from ns.api.schemas.canon import ConstraintClass, ConstitutionalRule

_SACRED_CONSTRAINTS: List[ConstitutionalRule] = [
    ConstitutionalRule(
        id="dignity_kernel",
        description="All operations must preserve human dignity invariants.",
        constraint_class=ConstraintClass.SACRED,
        invariant_ref="I3",
    ),
    ConstitutionalRule(
        id="append_only_lineage",
        description="Lineage Fabric is append-only; no record may be deleted or rewritten.",
        constraint_class=ConstraintClass.SACRED,
        invariant_ref="I2",
    ),
    ConstitutionalRule(
        id="receipt_requirement",
        description="Every canonical operation must emit a receipt.",
        constraint_class=ConstraintClass.SACRED,
        invariant_ref="I5",
    ),
    ConstitutionalRule(
        id="no_unauthorized_canon",
        description="Canon changes require hardware quorum; LLM authority over Canon is prohibited.",
        constraint_class=ConstraintClass.SACRED,
        invariant_ref="I4",
    ),
    ConstitutionalRule(
        id="no_deletion_rewriting",
        description="Supersession only; deletion and rewriting of canonical records are prohibited.",
        constraint_class=ConstraintClass.SACRED,
        invariant_ref="I10",
    ),
    ConstitutionalRule(
        id="no_identity_falsification",
        description="Identity of any agent or artifact must not be falsified.",
        constraint_class=ConstraintClass.SACRED,
        invariant_ref="I6",
    ),
    ConstitutionalRule(
        id="truthful_provenance",
        description="Provenance records must be accurate and hash-chain verified.",
        constraint_class=ConstraintClass.SACRED,
        invariant_ref="I5",
    ),
]


class CanonService:
    def __init__(self) -> None:
        self._rules: Dict[str, ConstitutionalRule] = {
            r.id: r for r in _SACRED_CONSTRAINTS
        }

    def get_all_rules(self) -> List[ConstitutionalRule]:
        return list(self._rules.values())

    def get_rule(self, rule_id: str) -> ConstitutionalRule:
        if rule_id not in self._rules:
            raise KeyError(f"Constitutional rule not found: {rule_id}")
        return self._rules[rule_id]

    def rule_count(self) -> int:
        return len(self._rules)
