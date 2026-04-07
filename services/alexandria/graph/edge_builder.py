"""
edge_builder.py — builds edges between atoms using word-overlap similarity.

Edge types:
  supports      — atoms reinforce each other (high similarity, compatible)
  contradicts   — one has negation/constraint signals vs the other
  refines       — one is a more specific sub-statement of the other
  depends_on    — temporal or causal dependency marker detected
"""

import re
import uuid
from dataclasses import dataclass
from typing import Optional

STOPWORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'shall', 'can', 'this', 'that',
    'it', 'its', 'i', 'we', 'you', 'he', 'she', 'they', 'my', 'our',
    'your', 'their', 'not', 'no', 'so', 'if', 'as', 'up', 'out', 'about',
}

CONTRADICTION_RE = re.compile(
    r'\b(not|never|no|cannot|can\'t|won\'t|however|but|despite|although|'
    r'contrary|opposed|blocked|fail|failed|issue|problem)\b',
    re.IGNORECASE
)

TEMPORAL_RE = re.compile(
    r'\b(after|then|because|therefore|since|when|once|before|following|'
    r'resulting|leading|causes|enables|requires|depends)\b',
    re.IGNORECASE
)


@dataclass
class Edge:
    id: str
    from_id: str
    to_id: str
    type: str

    def to_dict(self):
        return {"id": self.id, "from_id": self.from_id, "to_id": self.to_id, "type": self.type}


def tokenize(text: str) -> set[str]:
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    return {w for w in words if w not in STOPWORDS}


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def classify_edge(
    content_a: str,
    content_b: str,
    type_a: str,
    type_b: str,
    similarity: float,
) -> Optional[str]:
    """Determine edge type given two atom contents and their similarity score."""

    # Temporal / causal — check before similarity threshold
    if TEMPORAL_RE.search(content_a) or TEMPORAL_RE.search(content_b):
        if similarity > 0.15:
            return "depends_on"

    if similarity < 0.20:
        return None  # Not related enough

    # Contradiction: one is a constraint against the other's claim
    a_has_neg = bool(CONTRADICTION_RE.search(content_a))
    b_has_neg = bool(CONTRADICTION_RE.search(content_b))
    if a_has_neg != b_has_neg and similarity > 0.22:
        return "contradicts"

    # Refines: one is noticeably shorter (more specific) and high overlap
    len_ratio = min(len(content_a), len(content_b)) / max(len(content_a), len(content_b))
    if len_ratio < 0.55 and similarity > 0.35:
        return "refines"

    # Default: supports
    return "supports"


def build_edges_from_atoms(conn) -> dict:
    """
    Read all atoms, compute pairwise similarity, insert edges above threshold.
    Caps at 500 atoms to avoid O(n²) explosion in dev.
    """
    cur = conn.cursor()

    cur.execute("SELECT id, type, content FROM atoms ORDER BY created_at LIMIT 500")
    rows = cur.fetchall()

    atoms = [(str(r[0]), r[1], r[2]) for r in rows]

    # Pre-tokenize
    token_sets = [(aid, atype, acontent, tokenize(acontent))
                  for (aid, atype, acontent) in atoms]

    edges: list[Edge] = []
    seen: set[tuple] = set()

    for i, (aid, atype, acontent, atokens) in enumerate(token_sets):
        for j, (bid, btype, bcontent, btokens) in enumerate(token_sets):
            if i >= j:
                continue
            pair = (min(aid, bid), max(aid, bid))
            if pair in seen:
                continue
            seen.add(pair)

            sim = jaccard(atokens, btokens)
            edge_type = classify_edge(acontent, bcontent, atype, btype, sim)
            if edge_type:
                edges.append(Edge(
                    id=str(uuid.uuid4()),
                    from_id=aid,
                    to_id=bid,
                    type=edge_type,
                ))

    # Insert
    inserted = 0
    for edge in edges:
        cur.execute(
            "INSERT INTO edges (id, from_id, to_id, type) VALUES (%s, %s, %s, %s) "
            "ON CONFLICT DO NOTHING",
            (edge.id, edge.from_id, edge.to_id, edge.type)
        )
        inserted += 1

    conn.commit()
    cur.close()

    type_counts: dict[str, int] = {}
    for e in edges:
        type_counts[e.type] = type_counts.get(e.type, 0) + 1

    return {
        "atoms_loaded": len(atoms),
        "edges_created": inserted,
        "type_breakdown": type_counts,
    }
