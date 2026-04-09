"""
ProgramRuntime — 10 constitutional programs, 8-state machine, intent routing.

Programs are constitutional execution tracks. Each program has an 8-state
lifecycle and routes via keyword matching from founder intent.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid


# ── 8-State Machine ──────────────────────────────────────────────────────────

class ProgramState(str, Enum):
    DORMANT     = "dormant"
    ACTIVATED   = "activated"
    BRIEFING    = "briefing"
    EXECUTING   = "executing"
    REVIEW      = "review"
    PAUSED      = "paused"
    COMPLETED   = "completed"
    ARCHIVED    = "archived"

VALID_TRANSITIONS: dict[ProgramState, set[ProgramState]] = {
    ProgramState.DORMANT:   {ProgramState.ACTIVATED},
    ProgramState.ACTIVATED: {ProgramState.BRIEFING, ProgramState.PAUSED, ProgramState.ARCHIVED},
    ProgramState.BRIEFING:  {ProgramState.EXECUTING, ProgramState.PAUSED, ProgramState.ARCHIVED},
    ProgramState.EXECUTING: {ProgramState.REVIEW, ProgramState.PAUSED},
    ProgramState.REVIEW:    {ProgramState.EXECUTING, ProgramState.COMPLETED, ProgramState.ARCHIVED},
    ProgramState.PAUSED:    {ProgramState.ACTIVATED, ProgramState.ARCHIVED},
    ProgramState.COMPLETED: {ProgramState.ARCHIVED},
    ProgramState.ARCHIVED:  set(),
}


# ── Program ───────────────────────────────────────────────────────────────────

@dataclass
class Program:
    program_id: str
    name: str
    namespace: str
    description: str
    keywords: list[str]            # Intent routing keywords
    state: ProgramState = ProgramState.DORMANT
    instance_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_transition: Optional[str] = None
    context: dict = field(default_factory=dict)

    def can_transition(self, new_state: ProgramState) -> bool:
        return new_state in VALID_TRANSITIONS.get(self.state, set())

    def transition(self, new_state: ProgramState) -> bool:
        if not self.can_transition(new_state):
            return False
        self.state = new_state
        self.last_transition = datetime.now(timezone.utc).isoformat()
        return True

    def matches_intent(self, intent: str) -> bool:
        intent_lower = intent.lower()
        return any(kw in intent_lower for kw in self.keywords)

    def to_dict(self) -> dict:
        return {
            "program_id": self.program_id,
            "name": self.name,
            "namespace": self.namespace,
            "description": self.description,
            "state": self.state.value,
            "instance_id": self.instance_id,
            "created_at": self.created_at,
            "last_transition": self.last_transition,
        }


# ── 10 Constitutional Programs ───────────────────────────────────────────────

CANONICAL_PROGRAMS: list[Program] = [
    Program(
        program_id="prog_commercial",
        name="Commercial Track",
        namespace="commercial",
        description="Revenue generation, deals, pricing, sales motions",
        keywords=["revenue", "deal", "sales", "pricing", "contract", "customer", "close", "pipeline"],
    ),
    Program(
        program_id="prog_fundraising",
        name="Fundraising Track",
        namespace="fundraising",
        description="Investor outreach, term sheets, diligence, closing rounds",
        keywords=["fundraise", "investor", "round", "term sheet", "raise", "diligence", "vc", "angel", "seed", "series"],
    ),
    Program(
        program_id="prog_hiring",
        name="Hiring Track",
        namespace="hiring",
        description="Candidate pipeline, offers, onboarding, team building",
        keywords=["hire", "candidate", "offer", "onboard", "recruit", "interview", "team", "headcount"],
    ),
    Program(
        program_id="prog_partnership",
        name="Partnership Track",
        namespace="partner",
        description="Strategic partnerships, integrations, alliances, co-sell",
        keywords=["partner", "alliance", "integration", "co-sell", "reseller", "joint", "collaboration", "mou"],
    ),
    Program(
        program_id="prog_ma",
        name="M&A Track",
        namespace="ma",
        description="Acquisitions, mergers, due diligence, transaction closure",
        keywords=["acquisition", "merger", "acquire", "due diligence", "transaction", "loi", "close deal", "m&a"],
    ),
    Program(
        program_id="prog_advisor_san",
        name="Advisor / SAN Track",
        namespace="advisor",
        description="Advisor relationships, SAN territory mapping, claim registration",
        keywords=["advisor", "san", "territory", "claim", "whitespace", "filing", "licensing", "semantic territory"],
    ),
    Program(
        program_id="prog_customer_success",
        name="Customer Success Track",
        namespace="cs",
        description="Customer health, renewals, escalations, success plans",
        keywords=["customer success", "renewal", "churn", "health score", "escalation", "nps", "retention", "support"],
    ),
    Program(
        program_id="prog_product_feedback",
        name="Product Feedback Track",
        namespace="feedback",
        description="Feature requests, feedback processing, roadmap inputs",
        keywords=["feature request", "feedback", "roadmap", "product request", "user feedback", "wishlist", "bug report"],
    ),
    Program(
        program_id="prog_governance",
        name="Governance Track",
        namespace="gov",
        description="Decisions, constraints, policies, board-level governance",
        keywords=["governance", "decision", "policy", "constraint", "board", "resolution", "vote", "ratify"],
    ),
    Program(
        program_id="prog_knowledge",
        name="Knowledge Track",
        namespace="knowledge",
        description="Canon promotion, knowledge base management, semantic index",
        keywords=["knowledge", "canon", "promote", "learn", "document", "capture", "index", "semantic", "lexicon"],
    ),
]

assert len(CANONICAL_PROGRAMS) == 10, f"Expected 10 canonical programs, got {len(CANONICAL_PROGRAMS)}"


# ── Runtime ──────────────────────────────────────────────────────────────────

class ProgramRuntime:
    """
    Route founder intent to canonical programs.
    Manage program state transitions and activation.
    """

    def __init__(self):
        # Keyed by program_id
        self._programs: dict[str, Program] = {p.program_id: p for p in CANONICAL_PROGRAMS}

    def route_intent(self, intent: str) -> list[Program]:
        """Return programs that match the given intent (sorted by keyword density)."""
        matches = [p for p in self._programs.values() if p.matches_intent(intent)]
        # Sort by number of keyword hits (descending)
        def score(p: Program) -> int:
            return sum(1 for kw in p.keywords if kw in intent.lower())
        return sorted(matches, key=score, reverse=True)

    def activate(self, program_id: str, context: dict = {}) -> Optional[Program]:
        p = self._programs.get(program_id)
        if p and p.transition(ProgramState.ACTIVATED):
            p.context.update(context)
            return p
        return None

    def transition(self, program_id: str, new_state: ProgramState) -> bool:
        p = self._programs.get(program_id)
        if p:
            return p.transition(new_state)
        return False

    def get(self, program_id: str) -> Optional[Program]:
        return self._programs.get(program_id)

    def all(self) -> list[Program]:
        return list(self._programs.values())

    def active(self) -> list[Program]:
        return [p for p in self._programs.values()
                if p.state not in (ProgramState.DORMANT, ProgramState.ARCHIVED, ProgramState.COMPLETED)]

    def summary(self) -> dict:
        by_state: dict[str, list[str]] = {}
        for p in self._programs.values():
            by_state.setdefault(p.state.value, []).append(p.namespace)
        return {"programs": len(self._programs), "by_state": by_state}


_runtime = ProgramRuntime()

def get_program_runtime() -> ProgramRuntime:
    return _runtime
