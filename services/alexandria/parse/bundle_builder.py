"""Build parse_bundle objects from ParsedDocument."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

from parse.parser import ParsedDocument


MAX_CHUNK_CHARS = 1500
CHUNK_OVERLAP = 100


@dataclass
class ParseBundle:
    source_item_id: str
    parser_type: str          # pdf_native | markdown_native | text_native
    text_content: str
    structure_json: dict[str, Any]
    confidence: float
    chunk_count: int


def _chunk_text(text: str, size: int = MAX_CHUNK_CHARS, overlap: int = CHUNK_OVERLAP) -> list[str]:
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        start += size - overlap
    return chunks


def build(source_item_id: str, doc: ParsedDocument) -> ParseBundle:
    parser_type = f"{doc.file_type}_native"

    chunks = _chunk_text(doc.raw_text)

    structure: dict[str, Any] = {
        "file_type": doc.file_type,
        "page_count": doc.page_count,
        "confidence": doc.confidence,
        "chunk_count": len(chunks),
        "chunks": chunks,
    }

    if doc.file_type == "pdf":
        structure["pages"] = doc.pages
        structure["tables"] = doc.tables
        structure["paragraph_count"] = len(doc.paragraphs)

    elif doc.file_type == "markdown":
        structure["headings"] = doc.headings
        structure["lists"] = doc.lists
        structure["code_blocks"] = doc.code_blocks
        structure["paragraph_count"] = len(doc.paragraphs)

    else:  # text
        structure["paragraph_count"] = len(doc.paragraphs)
        structure["paragraphs"] = doc.paragraphs

    return ParseBundle(
        source_item_id=source_item_id,
        parser_type=parser_type,
        text_content=doc.raw_text,
        structure_json=structure,
        confidence=doc.confidence,
        chunk_count=len(chunks),
    )
