"""
atom_factory.py — converts parse bundle text into Story Atoms.

Atom types:
  program_candidate  — signals intent, planning, obligation
  constraint         — signals friction, opposition, limitation
  open_loop          — unresolved question or pending decision
  claim              — factual assertion (default)
  arc                — founder narrative arc (goal → effort → outcome)
"""

import re
import uuid
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Classification patterns
# ---------------------------------------------------------------------------

PROGRAM_CANDIDATE_RE = re.compile(
    r'\b(should|must|will|need to|needs to|have to|has to|plan to|planning to'
    r'|intend to|going to|aim to|want to|hoping to|required to)\b',
    re.IGNORECASE
)

CONSTRAINT_RE = re.compile(
    r'\b(but|however|yet|although|despite|unless|cannot|can\'t|won\'t|not|'
    r'never|blocked|issue|problem|challenge|risk|concern|limit|restrict)\b',
    re.IGNORECASE
)

OPEN_LOOP_RE = re.compile(
    r'(\?$|\bunclear\b|\bunknown\b|\bTBD\b|\bpending\b|\bwaiting\b|'
    r'\bneed to decide\b|\bnot yet\b|\bopen question\b)',
    re.IGNORECASE
)

# Founder arc seeds
GOAL_RE = re.compile(
    r'\b(goal|objective|vision|target|aim|mission|want to|plan to|intend to)\b',
    re.IGNORECASE
)
EFFORT_RE = re.compile(
    r'\b(build|building|create|creating|develop|developing|implement|implementing'
    r'|working on|writing|designing|shipping|running|launching|executing)\b',
    re.IGNORECASE
)
OUTCOME_RE = re.compile(
    r'\b(result|achieved|completed|done|shipped|launched|delivered|released'
    r'|finished|success|working|live|deployed|proved)\b',
    re.IGNORECASE
)

# Sentence splitter
SENT_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')

STOPWORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'shall', 'can', 'this', 'that',
    'it', 'its', 'i', 'we', 'you', 'he', 'she', 'they', 'my', 'our',
    'your', 'their', 'not', 'no', 'so', 'if', 'as', 'up', 'out', 'about',
}


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

@dataclass
class Atom:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "claim"
    content: str = ""
    source_id: Optional[str] = None  # source_item_id from parse_bundle
    bundle_id: Optional[str] = None  # parse_bundle.id
    arc_role: Optional[str] = None   # goal / effort / outcome (if arc candidate)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "content": self.content,
            "source_id": self.source_id,
        }


# ---------------------------------------------------------------------------
# Core extraction
# ---------------------------------------------------------------------------

def classify_sentence(sentence: str) -> tuple[str, Optional[str]]:
    """Return (atom_type, arc_role|None)."""
    s = sentence.strip()
    if not s:
        return "claim", None

    # Open loop first — overrides everything
    if OPEN_LOOP_RE.search(s):
        return "open_loop", None

    # Constraint
    if CONSTRAINT_RE.search(s):
        return "constraint", None

    # Program candidate
    if PROGRAM_CANDIDATE_RE.search(s):
        # Also check arc role
        arc_role = None
        if GOAL_RE.search(s):
            arc_role = "goal"
        elif EFFORT_RE.search(s):
            arc_role = "effort"
        return "program_candidate", arc_role

    # Arc roles within plain claims
    if GOAL_RE.search(s):
        return "claim", "goal"
    if EFFORT_RE.search(s):
        return "claim", "effort"
    if OUTCOME_RE.search(s):
        return "claim", "outcome"

    return "claim", None


def extract_atoms_from_text(
    text: str,
    source_item_id: Optional[str] = None,
    bundle_id: Optional[str] = None,
    min_len: int = 15,
) -> list[Atom]:
    """Split text into sentences and classify each as an Atom."""
    if not text:
        return []

    sentences = SENT_SPLIT_RE.split(text.strip())
    atoms: list[Atom] = []

    for sent in sentences:
        sent = sent.strip()
        if len(sent) < min_len:
            continue
        atom_type, arc_role = classify_sentence(sent)
        atoms.append(Atom(
            type=atom_type,
            content=sent,
            source_id=source_item_id,
            bundle_id=bundle_id,
            arc_role=arc_role,
        ))

    return atoms


def detect_founder_arcs(atoms: list[Atom]) -> list[Atom]:
    """
    Scan atom list for goal → effort → outcome narrative sequences.
    Creates a synthetic 'arc' Atom for each complete sequence found.
    """
    arc_atoms: list[Atom] = []
    goals = [a for a in atoms if a.arc_role == "goal"]
    efforts = [a for a in atoms if a.arc_role == "effort"]
    outcomes = [a for a in atoms if a.arc_role == "outcome"]

    for g in goals:
        for e in efforts:
            for o in outcomes:
                summary = (
                    f"[FOUNDER ARC] Goal: {g.content[:80]} | "
                    f"Effort: {e.content[:80]} | "
                    f"Outcome: {o.content[:80]}"
                )
                arc_atoms.append(Atom(
                    type="arc",
                    content=summary,
                    source_id=g.source_id,
                    bundle_id=g.bundle_id,
                    arc_role=None,
                ))
    return arc_atoms


# ---------------------------------------------------------------------------
# DB integration
# ---------------------------------------------------------------------------

def build_atoms_from_bundles(conn) -> dict:
    """
    Read all parse_bundles with text_content, extract atoms,
    insert into atoms table. Returns summary.
    """
    from db import get_cursor

    cur = conn.cursor()

    # Fetch bundles
    cur.execute(
        "SELECT id, source_item_id, text_content FROM parse_bundles "
        "WHERE text_content IS NOT NULL AND text_content != ''"
    )
    bundles = cur.fetchall()

    all_atoms: list[Atom] = []
    for bundle in bundles:
        bundle_id = str(bundle[0])
        source_item_id = str(bundle[1]) if bundle[1] else None
        text = bundle[2]
        atoms = extract_atoms_from_text(text, source_item_id, bundle_id)
        all_atoms.extend(atoms)

    # Detect arcs
    arc_atoms = detect_founder_arcs(all_atoms)
    all_atoms.extend(arc_atoms)

    # Insert
    inserted = 0
    for atom in all_atoms:
        cur.execute(
            "INSERT INTO atoms (id, type, content, source_id) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT DO NOTHING",
            (atom.id, atom.type, atom.content, atom.source_id)
        )
        inserted += 1

    conn.commit()
    cur.close()

    type_counts: dict[str, int] = {}
    for a in all_atoms:
        type_counts[a.type] = type_counts.get(a.type, 0) + 1

    return {
        "bundles_processed": len(bundles),
        "atoms_created": inserted,
        "type_breakdown": type_counts,
        "arcs_detected": len(arc_atoms),
    }
