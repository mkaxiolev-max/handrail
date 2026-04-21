"""Category 1 — Perception (COMET-equivalent). AXIOLEV © 2026."""
from services.omega_logos.layers.perception import cluster, background_hypotheses

def test_1_1_heterogeneous_tabs_cluster():
    tabs = [
        {"url":"https://sec.gov/filing","title":"SEC 10-K"},
        {"url":"https://finance.yahoo.com/q?s=AAPL","title":"AAPL"},
        {"url":"https://github.com/org/repo/pull/1","title":"PR"},
        {"url":"https://stackoverflow.com/q","title":"python"},
        {"url":"https://docs.google.com/doc","title":"notes"},
        {"url":"https://notion.so/page","title":"spec"},
        {"url":"https://figma.com/file","title":"design"},
        {"url":"https://dribbble.com/shots","title":"tailwind"},
        {"url":"https://news.ycombinator.com","title":"HN"},
        {"url":"https://example.com","title":"random"},
    ]
    c = cluster(tabs)
    assert "finance" in c and "code" in c and "docs" in c and "ui" in c
    # Each known family must have at least one tab
    for fam in ["finance","code","docs","ui"]:
        assert len(c[fam]) >= 1, f"empty cluster for {fam}"

def test_1_2_background_hypotheses():
    h = background_hypotheses({"earnings":"up","users":"flat","churn":"down"})
    assert len(h) >= 1
    assert all("hypothesis" in x for x in h)
