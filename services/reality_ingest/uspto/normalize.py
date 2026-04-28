from __future__ import annotations
from datetime import datetime
import logging
from typing import Optional
from services.reality_ingest.schema import RealityObject, EpistemicClass, FieldProvenance

logger = logging.getLogger(__name__)


def normalize(record: dict, raw_pointer: str, receipt_id: str) -> RealityObject | None:
    if not record.get("id"):
        return None
    typ = record.get("type", "patent_grant")
    epistemic = {
        "patent_grant": EpistemicClass.OBSERVED_FACT,
        "application":  EpistemicClass.REPORTED_CLAIM,
        "assignment":   EpistemicClass.LEGAL_STATUS_EVENT,
    }.get(typ, EpistemicClass.REPORTED_CLAIM)
    provenance = [FieldProvenance(field=f, present=bool(record.get(f)),
                                  reason=None if record.get(f) else "absent_in_source")
                  for f in ["title", "abstract", "filing_date", "grant_date"]]
    try:
        return RealityObject(
            id=f"USPTO-{record['id']}",
            source="USPTO", type=typ,
            title=record.get("title"), abstract=record.get("abstract"),
            claims=record.get("claims", []),
            inventors=record.get("inventors", []),
            assignees=record.get("assignees", []),
            filing_date=_parse_date(record.get("filing_date")),
            publication_date=_parse_date(record.get("publication_date")),
            grant_date=_parse_date(record.get("grant_date")),
            cpc_codes=record.get("cpc_codes", []),
            citations=record.get("citations", []),
            family_ids=[],
            epistemic_class=epistemic,
            raw_source_pointer=raw_pointer,
            ingestion_receipt_id=receipt_id,
            field_provenance=provenance,
        )
    except Exception as e:
        logger.debug(f"normalize failed: {e}")
        return None


def _parse_date(s: Optional[str]):
    if not s: return None
    for fmt in ("%Y%m%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except ValueError:
            continue
    return None
