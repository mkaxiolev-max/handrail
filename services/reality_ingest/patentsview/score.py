from datetime import datetime, timezone
from services.reality_ingest.schema import RealityObject

def score(obj: RealityObject) -> RealityObject:
    obj.credibility = 0.92
    cite_count = len(obj.citations)
    obj.novelty = 1.0 / (1.0 + cite_count)
    obj.impact = min(1.0, cite_count / 50.0) if cite_count else 0.10
    obj.technical_validity = 0.85
    if obj.grant_date:
        days_old = (datetime.now(timezone.utc) - obj.grant_date.replace(tzinfo=timezone.utc)).days
        obj.narrative_momentum = max(0.0, 1.0 - days_old / 365.0)
    return obj
