from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4
from .events import get_event_spine

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class DesiredState:
    description: str
    measurable_criteria: list[str] = field(default_factory=list)
    current_distance: float = 1.0

@dataclass
class ConstraintEnvelope:
    hard_constraints: list[str] = field(default_factory=list)
    soft_constraints: list[str] = field(default_factory=list)

@dataclass
class CathedralRevision:
    revision_id: str = field(default_factory=lambda: str(uuid4()))
    revised_at: str = field(default_factory=utc_now)
    author: str = "founder"
    change_summary: str = ""
    evidence_that_prompted_revision: list[str] = field(default_factory=list)

@dataclass
class CathedralArtifact:
    cathedral_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    domain: str = ""
    desired_state: DesiredState = field(default_factory=lambda: DesiredState(""))
    constraint_envelope: ConstraintEnvelope = field(default_factory=ConstraintEnvelope)
    revision_history: list[CathedralRevision] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    active: bool = True

    def revise(self, author: str, change_summary: str, evidence: list[str] | None = None) -> CathedralRevision:
        rev = CathedralRevision(author=author, change_summary=change_summary,
                                evidence_that_prompted_revision=evidence or [])
        self.revision_history.append(rev)
        get_event_spine().append("cathedral_revised", {
            "entity_id": self.cathedral_id, "cathedral_name": self.name,
            "revision_id": rev.revision_id, "change_summary": change_summary,
        }, agent_id=author)
        return rev

    def current_version(self) -> int:
        return len(self.revision_history) + 1

    def progress(self) -> float:
        return self.desired_state.current_distance

class CathedralRegistry:
    def __init__(self):
        self._cathedrals: dict[str, CathedralArtifact] = {}

    def register(self, cathedral: CathedralArtifact) -> CathedralArtifact:
        self._cathedrals[cathedral.cathedral_id] = cathedral
        get_event_spine().append("cathedral_registered",
            {"entity_id": cathedral.cathedral_id, "name": cathedral.name}, agent_id="founder")
        return cathedral

    def get(self, cathedral_id: str) -> CathedralArtifact | None:
        return self._cathedrals.get(cathedral_id)

    def list_active(self) -> list[CathedralArtifact]:
        return [c for c in self._cathedrals.values() if c.active]

_registry = CathedralRegistry()
def get_cathedral_registry() -> CathedralRegistry:
    return _registry
