# Copyright © 2026 Axiolev. All rights reserved.
"""
Corpus Ingest CPS Lane — corpus.ingest_all
file_scan → chunk → atom write → receipt

Source:  /Volumes/NSExternal/alexandria/raw_ingest/mike_corpus_v1/
Atoms:   /Volumes/NSExternal/alexandria/atoms/
Receipts:/Volumes/NSExternal/receipts/

All writes go direct to Alexandria paths — NOT through Mac adapter.
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

_SOURCE_DIR   = Path("/Volumes/NSExternal/alexandria/raw_ingest/mike_corpus_v1")
_ATOMS_DIR    = Path("/Volumes/NSExternal/alexandria/atoms")
_RECEIPTS_DIR = Path("/Volumes/NSExternal/receipts")

_TEXT_SUFFIXES = {".txt", ".md", ".json"}
_PDF_SUFFIX    = ".pdf"

# ~500 tokens ≈ 2000 characters
_CHUNK_CHARS = 2000


def _ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_text(path: Path) -> str | None:
    """Return text content or None if binary/unreadable."""
    if path.suffix.lower() in _TEXT_SUFFIXES:
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return None

    if path.suffix.lower() == _PDF_SUFFIX:
        # Try pdfminer, fall back to PyPDF2, fall back to skip
        try:
            from pdfminer.high_level import extract_text as _pdf_extract
            return _pdf_extract(str(path))
        except ImportError:
            pass
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(str(path))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages)
        except Exception:
            pass
        return None

    return None


def _chunk(text: str) -> list[str]:
    """Split text into ~500-token (~2000-char) chunks, respecting paragraph breaks."""
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + _CHUNK_CHARS, length)
        # Try to break on a newline near the boundary
        if end < length:
            nl = text.rfind("\n", start, end)
            if nl > start + _CHUNK_CHARS // 2:
                end = nl + 1
        segment = text[start:end].strip()
        if segment:
            chunks.append(segment)
        start = end
    return chunks


def _write_atom(atom: dict) -> None:
    _ATOMS_DIR.mkdir(parents=True, exist_ok=True)
    ((_ATOMS_DIR) / f"{atom['atom_id']}.json").write_text(
        json.dumps(atom, ensure_ascii=False, indent=2)
    )


def _write_receipt(receipt: dict) -> None:
    _RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
    ((_RECEIPTS_DIR) / f"{receipt['receipt_id']}.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2)
    )


def _op_corpus_ingest_all(args: dict, _policy) -> dict:
    """
    Walk source dir → chunk all text files → write atoms + receipts.
    Returns {ok, files_scanned, chunks_created, atoms_written, receipts_issued}.
    """
    if not _SOURCE_DIR.exists():
        return {
            "ok": False,
            "error": f"source dir not found: {_SOURCE_DIR}",
            "files_scanned": 0,
            "chunks_created": 0,
            "atoms_written": 0,
            "receipts_issued": 0,
        }

    supported = _TEXT_SUFFIXES | {_PDF_SUFFIX}
    all_files = [
        f for f in sorted(_SOURCE_DIR.rglob("*"))
        if f.is_file() and f.suffix.lower() in supported
    ]

    files_scanned   = 0
    chunks_created  = 0
    atoms_written   = 0
    receipts_issued = 0
    skipped_files: list[str] = []

    ingested_at = _ts()

    for file_path in all_files:
        files_scanned += 1
        text = _read_text(file_path)
        if text is None:
            skipped_files.append(str(file_path.name))
            continue

        chunks = _chunk(text)
        chunks_created += len(chunks)

        rel_path = str(file_path.relative_to(_SOURCE_DIR))

        for idx, chunk_text in enumerate(chunks):
            atom_id = str(uuid.uuid4())
            atom = {
                "atom_id":      atom_id,
                "source_file":  rel_path,
                "chunk_index":  idx,
                "text":         chunk_text,
                "ingested_at":  ingested_at,
            }
            _write_atom(atom)
            atoms_written += 1

            receipt = {
                "receipt_id": f"ingest_{atom_id}",
                "event_type": "corpus.atom_ingested",
                "atom_id":    atom_id,
                "source_file": rel_path,
                "chunk_index": idx,
                "timestamp":  ingested_at,
            }
            _write_receipt(receipt)
            receipts_issued += 1

    return {
        "ok":              True,
        "files_scanned":   files_scanned,
        "chunks_created":  chunks_created,
        "atoms_written":   atoms_written,
        "receipts_issued": receipts_issued,
        "skipped_files":   skipped_files,
        "source":          str(_SOURCE_DIR),
        "atoms_dest":      str(_ATOMS_DIR),
    }


# ---------------------------------------------------------------------------
# Registry export
# ---------------------------------------------------------------------------

INGEST_OPS: dict[str, Any] = {
    "corpus.ingest_all": _op_corpus_ingest_all,
}
