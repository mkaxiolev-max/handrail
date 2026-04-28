from datetime import datetime, timezone
from services.reality_ingest.schema import RealityObject


def score(obj: RealityObject) -> RealityObject:
    obj.credibility = 0.95
    cite_count = len(obj.citations)
    obj.novelty = 1.0 / (1.0 + cite_count)
    obj.impact = 0.10 if cite_count == 0 else min(1.0, cite_count / 50.0)
    obj.technical_validity = 0.9 if obj.type == "patent_grant" else 0.6
    if obj.grant_date:
        days_old = (datetime.now(timezone.utc) - obj.grant_date.replace(tzinfo=timezone.utc)).days
        obj.narrative_momentum = max(0.0, 1.0 - days_old / 365.0)
    else:
        obj.narrative_momentum = 0.0
    return obj
