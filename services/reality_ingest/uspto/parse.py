from __future__ import annotations
import logging, zipfile
from pathlib import Path
from typing import Iterator
from lxml import etree

logger = logging.getLogger(__name__)


def iter_grant_documents(zip_path: Path) -> Iterator[bytes]:
    with zipfile.ZipFile(zip_path) as z:
        xml_names = [n for n in z.namelist() if n.endswith(".xml")]
        if not xml_names:
            return
        with z.open(xml_names[0]) as f:
            buf = b""
            for line in f:
                if line.startswith(b"<?xml") and buf:
                    yield buf; buf = b""
                buf += line
            if buf:
                yield buf


def parse_grant(xml_bytes: bytes) -> dict | None:
    try:
        root = etree.fromstring(xml_bytes)
    except Exception:
        return None
    bib = root.find(".//us-bibliographic-data-grant")
    if bib is None:
        return None
    record = {
        "id": _text(bib.find(".//publication-reference/document-id/doc-number")),
        "type": "patent_grant",
        "title": _text(bib.find(".//invention-title")),
        "filing_date": _text(bib.find(".//application-reference/document-id/date")),
        "grant_date": _text(bib.find(".//publication-reference/document-id/date")),
        "publication_date": _text(bib.find(".//publication-reference/document-id/date")),
        "abstract": _join_text(root.findall(".//abstract//p")),
        "claims": [_join_text([c]) for c in root.findall(".//claim")],
        "inventors": [
            f"{_text(i.find('.//first-name'))} {_text(i.find('.//last-name'))}".strip()
            for i in (bib.findall(".//inventors/inventor") or []) if i is not None
        ],
        "assignees": [
            _text(a.find(".//orgname")) or _text(a.find(".//last-name"))
            for a in (bib.findall(".//assignees/assignee") or [])
        ],
        "cpc_codes": [
            _format_cpc(c) for c in (bib.findall(".//classifications-cpc/main-cpc/classification-cpc") or [])
        ] + [
            _format_cpc(c) for c in (bib.findall(".//classifications-cpc/further-cpc/classification-cpc") or [])
        ],
        "citations": [
            _text(c.find(".//doc-number"))
            for c in (bib.findall(".//us-references-cited/us-citation/patcit/document-id") or [])
            if _text(c.find(".//doc-number"))
        ],
    }
    if not record["id"]:
        return None
    record["inventors"] = [x for x in record["inventors"] if x and x.strip()]
    record["assignees"] = [x for x in record["assignees"] if x and x.strip()]
    record["cpc_codes"] = [x for x in record["cpc_codes"] if x]
    return record


def _text(el) -> str | None:
    if el is None: return None
    t = (el.text or "").strip()
    return t if t else None


def _join_text(elems) -> str | None:
    if not elems: return None
    s = " ".join("".join(e.itertext()).strip() for e in elems if e is not None)
    return s if s.strip() else None


def _format_cpc(el) -> str | None:
    parts = [_text(el.find(t)) or "" for t in ("section","class","subclass","main-group","subgroup")]
    code = f"{''.join(parts[:4])}/{parts[4]}".strip("/")
    return code if code else None
