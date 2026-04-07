"""Native document parsers: .txt, .md, .pdf"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ParsedDocument:
    file_type: str
    raw_text: str
    pages: list[dict[str, Any]] = field(default_factory=list)
    headings: list[dict[str, Any]] = field(default_factory=list)
    tables: list[dict[str, Any]] = field(default_factory=list)
    code_blocks: list[str] = field(default_factory=list)
    lists: list[list[str]] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)
    page_count: int = 0
    confidence: float = 1.0


def detect_type(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix in (".md", ".markdown"):
        return "markdown"
    return "text"


def parse_text(path: str) -> ParsedDocument:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    return ParsedDocument(
        file_type="text",
        raw_text=text,
        paragraphs=paragraphs,
        page_count=1,
        confidence=1.0,
    )


def parse_markdown(path: str) -> ParsedDocument:
    text = Path(path).read_text(encoding="utf-8", errors="replace")

    headings: list[dict] = []
    lists: list[list[str]] = []
    code_blocks: list[str] = []
    paragraphs: list[str] = []

    current_list: list[str] = []
    in_code = False
    code_buf: list[str] = []
    para_buf: list[str] = []

    for line in text.splitlines():
        # Code fence
        if line.startswith("```"):
            if in_code:
                code_blocks.append("\n".join(code_buf))
                code_buf = []
                in_code = False
            else:
                if para_buf:
                    paragraphs.append(" ".join(para_buf))
                    para_buf = []
                in_code = True
            continue
        if in_code:
            code_buf.append(line)
            continue

        # Heading
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            if current_list:
                lists.append(current_list)
                current_list = []
            if para_buf:
                paragraphs.append(" ".join(para_buf))
                para_buf = []
            headings.append({"level": len(m.group(1)), "text": m.group(2).strip()})
            continue

        # List item
        if re.match(r"^[-*+]\s+|^\d+\.\s+", line):
            if para_buf:
                paragraphs.append(" ".join(para_buf))
                para_buf = []
            current_list.append(re.sub(r"^[-*+\d.]+\s+", "", line).strip())
            continue

        # Blank line — flush list or paragraph
        if not line.strip():
            if current_list:
                lists.append(current_list)
                current_list = []
            if para_buf:
                paragraphs.append(" ".join(para_buf))
                para_buf = []
            continue

        # Regular text
        if current_list:
            lists.append(current_list)
            current_list = []
        para_buf.append(line.strip())

    # Flush
    if current_list:
        lists.append(current_list)
    if para_buf:
        paragraphs.append(" ".join(para_buf))
    if code_buf:
        code_blocks.append("\n".join(code_buf))

    return ParsedDocument(
        file_type="markdown",
        raw_text=text,
        headings=headings,
        lists=lists,
        code_blocks=code_blocks,
        paragraphs=paragraphs,
        page_count=1,
        confidence=1.0,
    )


def parse_pdf(path: str) -> ParsedDocument:
    try:
        import pdfplumber
    except ImportError:
        raise RuntimeError("pdfplumber not installed — run: pip install pdfplumber")

    pages: list[dict] = []
    all_text_parts: list[str] = []
    all_tables: list[dict] = []

    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            tables = page.extract_tables() or []
            serialized_tables = []
            for t in tables:
                serialized_tables.append(
                    {"rows": [[cell or "" for cell in row] for row in t]}
                )
                all_tables.append({"page": i + 1, "rows": serialized_tables[-1]["rows"]})

            pages.append({"page": i + 1, "text": text, "tables": serialized_tables})
            if text:
                all_text_parts.append(text)

    raw_text = "\n\n".join(all_text_parts)
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", raw_text) if p.strip()]

    return ParsedDocument(
        file_type="pdf",
        raw_text=raw_text,
        pages=pages,
        tables=all_tables,
        paragraphs=paragraphs,
        page_count=len(pages),
        confidence=0.95,
    )


def parse(path: str) -> ParsedDocument:
    ftype = detect_type(path)
    if ftype == "pdf":
        return parse_pdf(path)
    if ftype == "markdown":
        return parse_markdown(path)
    return parse_text(path)
