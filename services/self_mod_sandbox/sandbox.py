"""Self-Modification Sandbox — controlled self-modification with recursion guard."""
from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

FORBIDDEN_PATHS = ("services/self_mod_sandbox/", "tools/ns_test_ontology/")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class ModificationProposal:
    path: str
    content_hash: str
    proposed_at: str
    approved: bool = False
    rejection_reason: str = ""


@dataclass
class SandboxAuditEntry:
    path: str
    action: str
    approved: bool
    ts: str
    content_hash: str


class SelfModSandbox:
    def __init__(self, root: str | Path = "."):
        self.root = Path(root)
        self._audit: list[SandboxAuditEntry] = []
        self._proposals: dict[str, ModificationProposal] = {}

    def _is_forbidden(self, path: str) -> bool:
        normalized = str(path).replace("\\", "/")
        return any(f in normalized for f in FORBIDDEN_PATHS)

    def propose_modification(self, path: str, content: str) -> ModificationProposal:
        h = hashlib.sha256(content.encode()).hexdigest()[:16]
        if self._is_forbidden(path):
            p = ModificationProposal(path, h, _ts(), approved=False,
                                     rejection_reason="forbidden_path")
            self._audit.append(SandboxAuditEntry(path, "propose", False, _ts(), h))
            self._proposals[path] = p
            raise ValueError(f"Path '{path}' is in forbidden zone — recursion guard active")
        p = ModificationProposal(path, h, _ts(), approved=True)
        self._audit.append(SandboxAuditEntry(path, "propose", True, _ts(), h))
        self._proposals[path] = p
        return p

    def get_audit_log(self) -> list[dict]:
        from dataclasses import asdict
        return [asdict(e) for e in self._audit]

    def audit_length(self) -> int:
        return len(self._audit)

    def approved_proposals(self) -> list[ModificationProposal]:
        return [p for p in self._proposals.values() if p.approved]

    def rejected_proposals(self) -> list[ModificationProposal]:
        return [p for p in self._proposals.values() if not p.approved]
