from __future__ import annotations
from dataclasses import dataclass, field
from uuid import uuid4
from .parser import ParsedDocument, Chunk

@dataclass
class ProgramCandidate:
    candidate_id: str = field(default_factory=lambda: str(uuid4()))
    source_document_id: str = ""
    source_chunks: list[str] = field(default_factory=list)
    program_name: str = ""
    program_type: str = ""
    extracted_steps: list[str] = field(default_factory=list)
    extracted_constraints: list[str] = field(default_factory=list)
    confidence: float = 0.5
    requires_review: bool = True

class ProgramExtractor:
    PROGRAM_TYPE_SIGNALS = {
        "boot":        ["boot sequence", "startup", "initialize", "cold boot"],
        "ingestion":   ["ingest", "parse", "extract", "corpus", "document intake"],
        "governance":  ["policy", "amendment", "charter", "governance", "approval"],
        "operational": ["daily", "weekly", "shutdown", "backup", "sync"],
    }

    def extract(self, doc: ParsedDocument) -> list[ProgramCandidate]:
        signal_chunks = doc.program_signal_chunks()
        if not signal_chunks:
            return []
        type_groups: dict[str, list[Chunk]] = {}
        for chunk in signal_chunks:
            ptype = self._classify(chunk.text)
            type_groups.setdefault(ptype, []).append(chunk)
        return [
            ProgramCandidate(
                source_document_id=doc.document_id,
                source_chunks=[c.chunk_id for c in chunks],
                program_name=f"{doc.title or 'unknown'}_{ptype}_program",
                program_type=ptype,
                extracted_steps=[c.text[:100] for c in chunks],
                extracted_constraints=doc.constraint_candidates()[:5],
                confidence=min(0.5 + len(chunks) * 0.05, 0.9),
            )
            for ptype, chunks in type_groups.items()
        ]

    def _classify(self, text: str) -> str:
        tl = text.lower()
        for ptype, signals in self.PROGRAM_TYPE_SIGNALS.items():
            if any(s in tl for s in signals):
                return ptype
        return "unknown"
