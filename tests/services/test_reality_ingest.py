"""C21 — Reality ingest + voice + drive delta tests. I6."""
from services.reality_ingest.ingest import RealityIngestPipeline, SourceType, IngestEvent


def test_ingest_voice():
    p = RealityIngestPipeline()
    e = p.ingest(SourceType.VOICE, "hello world")
    assert e.source == SourceType.VOICE
    assert e.processed is False


def test_ingest_document():
    p = RealityIngestPipeline()
    e = p.ingest(SourceType.DOCUMENT, "doc content")
    assert isinstance(e, IngestEvent)


def test_ingest_drive_delta():
    p = RealityIngestPipeline()
    e = p.ingest(SourceType.DRIVE_DELTA, "file changed")
    assert e.hash != ""


def test_process_pending():
    p = RealityIngestPipeline()
    p.ingest(SourceType.VOICE, "a")
    p.ingest(SourceType.API, "b")
    count = p.process_pending()
    assert count == 2


def test_event_count_by_source():
    p = RealityIngestPipeline()
    p.ingest(SourceType.VOICE, "v1")
    p.ingest(SourceType.VOICE, "v2")
    p.ingest(SourceType.API, "a1")
    assert p.event_count(SourceType.VOICE) == 2


def test_recent_returns_latest():
    p = RealityIngestPipeline()
    for i in range(5):
        p.ingest(SourceType.DOCUMENT, f"doc{i}")
    r = p.recent(3)
    assert len(r) == 3


def test_event_id_unique():
    p = RealityIngestPipeline()
    e1 = p.ingest(SourceType.VOICE, "x")
    e2 = p.ingest(SourceType.VOICE, "y")
    assert e1.event_id != e2.event_id
