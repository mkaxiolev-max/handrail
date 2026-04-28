from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, Dict
from services.reality_ingest.schema import (
    RealityObject, EpistemicClass, SourceLane, SourceTier, FieldProvenance,
)


def parse_date(s: Optional[str]):
    if not s or s.strip() in ("", "NULL", "\\N"):
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def normalize_patent_row(row: dict, source_url: str, source_receipt_id: str,
                         ingestion_receipt_id: str,
                         join: Optional[Dict[str, list]] = None) -> Optional[RealityObject]:
    pid = (row.get("patent_id") or row.get("id") or "").strip()
    if not pid:
        return None
    join = join or {}
    title = row.get("patent_title") or row.get("title")
    abstract = row.get("patent_abstract") or row.get("abstract")
    grant_date = parse_date(row.get("patent_date") or row.get("grant_date"))
    return RealityObject(
        id=f"USPTO-{pid}",
        source="USPTO",
        type="patent_grant",
        source_lane=SourceLane.PATENTSVIEW_S3,
        source_tier=SourceTier.DERIVED_PUBLIC,
        source_url=source_url,
        source_resolved_at=datetime.now(timezone.utc),
        source_receipt_id=source_receipt_id,
        title=title,
        abstract=abstract,
        claims=[],
        inventors=join.get("inventors", []),
        assignees=join.get("assignees", []),
        cpc_codes=join.get("cpc", []),
        citations=join.get("citations", []),
        filing_date=parse_date(row.get("filing_date")),
        grant_date=grant_date,
        publication_date=grant_date,
        epistemic_class=EpistemicClass.OBSERVED_FACT,
        raw_source_pointer=source_url,
        ingestion_receipt_id=ingestion_receipt_id,
        field_provenance=[
            FieldProvenance(field=f, present=bool(row.get(f)),
                            reason=None if row.get(f) else "absent_in_tsv")
            for f in ("patent_title", "patent_abstract", "patent_date")
        ],
    )
