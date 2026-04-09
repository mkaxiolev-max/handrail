from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

class ParseClass(str, Enum):
    text_native = "text_native"
    office_native = "office_native"
    pdf_text_native = "pdf_text_native"
    pdf_image_native = "pdf_image_native"
    tabular = "tabular"
    visual_diagram = "visual_diagram"
    audio_video = "audio_video"
    mixed_bundle = "mixed_bundle"
    unknown = "unknown"

@dataclass
class Chunk:
    chunk_id: str = field(default_factory=lambda: str(uuid4()))
    text: str = ""
    position: int = 0
    section_id: str = ""
    claim_candidates: list[str] = field(default_factory=list)
    constraint_candidates: list[str] = field(default_factory=list)
    program_signal: bool = False

@dataclass
class Section:
    section_id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    level: int = 1
    chunks: list[Chunk] = field(default_factory=list)

@dataclass
class ParsedDocument:
    document_id: str = field(default_factory=lambda: str(uuid4()))
    source_path: str = ""
    parse_class: ParseClass = ParseClass.unknown
    title: str = ""
    sections: list[Section] = field(default_factory=list)
    tables: list[dict] = field(default_factory=list)
    figure_refs: list[str] = field(default_factory=list)
    citation_refs: list[str] = field(default_factory=list)
    raw_text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def all_chunks(self) -> list[Chunk]:
        return [c for s in self.sections for c in s.chunks]

    def program_signal_chunks(self) -> list[Chunk]:
        return [c for c in self.all_chunks() if c.program_signal]

    def claim_candidates(self) -> list[str]:
        return [cc for c in self.all_chunks() for cc in c.claim_candidates]

    def constraint_candidates(self) -> list[str]:
        return [cc for c in self.all_chunks() for cc in c.constraint_candidates]

class DocumentParser:
    PROCEDURE_SIGNALS = [
        "step ", "steps:", "procedure", "algorithm", "if ", "when ",
        "first,", "then,", "finally,", "do not", "must ", "shall ",
        "run ", "execute", "invoke", "call ", "boot ", "initialize",
    ]
    CONSTRAINT_SIGNALS = [
        "must not", "never ", "prohibited", "forbidden", "invariant",
        "always ", "required", "mandatory", "enforce", "cannot ",
    ]

    def classify(self, source_path: str, content: str | None = None) -> ParseClass:
        p = source_path.lower()
        if p.endswith((".md", ".txt", ".rst")): return ParseClass.text_native
        elif p.endswith((".docx", ".xlsx", ".pptx")): return ParseClass.office_native
        elif p.endswith(".pdf"): return ParseClass.pdf_text_native
        elif p.endswith((".csv", ".tsv")): return ParseClass.tabular
        elif p.endswith((".png", ".jpg", ".svg")): return ParseClass.visual_diagram
        elif p.endswith((".mp3", ".mp4", ".wav")): return ParseClass.audio_video
        return ParseClass.unknown

    def parse_text(self, source_path: str, content: str) -> ParsedDocument:
        doc = ParsedDocument(source_path=source_path,
                             parse_class=self.classify(source_path, content),
                             raw_text=content)
        current_section = Section(title="(root)", level=0)
        current_lines: list[str] = []
        for line in content.split("\n"):
            if line.startswith("#"):
                if current_lines:
                    current_section.chunks = self._build_chunks(current_lines, current_section.section_id)
                    doc.sections.append(current_section)
                level = len(line) - len(line.lstrip("#"))
                current_section = Section(title=line.lstrip("#").strip(), level=level)
                current_lines = []
            elif line.strip():
                current_lines.append(line)
        if current_lines:
            current_section.chunks = self._build_chunks(current_lines, current_section.section_id)
        doc.sections.append(current_section)
        return doc

    def _build_chunks(self, lines: list[str], section_id: str) -> list[Chunk]:
        text = " ".join(lines)
        chunks = []
        for i in range(0, len(text), 200):
            ct = text[i:i+200]
            chunk = Chunk(text=ct, position=i, section_id=section_id,
                program_signal=any(s in ct.lower() for s in self.PROCEDURE_SIGNALS),
                constraint_candidates=[ct[j:j+80] for j in range(0, len(ct), 80)
                    if any(s in ct[j:j+80].lower() for s in self.CONSTRAINT_SIGNALS)])
            chunks.append(chunk)
        return chunks
