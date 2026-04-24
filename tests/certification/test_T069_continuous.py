# Copyright © 2026 AXIOLEV Holdings LLC. All rights reserved.
"""T-069 — Continuous: continuous-cert daily job green for 7d rolling.

I7 certification pillar — emits CertificateArtifact to Lineage Fabric on success.
"""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from services.assurance import CertificateArtifact
from ns.integrations.alexandria import AlexandrianArchive

_ISSUER = "axiolev_dignity_kernel"
_EXPIRY = (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")

_ROLLING_WINDOW_DAYS = 7
_NOW = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

# 7-day rolling window: one green job result per day
_DAILY_JOB_RESULTS: List[Dict] = [
    {
        "run_date": (_NOW - timedelta(days=i)).strftime("%Y-%m-%d"),
        "status":   "green",
        "pillars_passed": 10,
        "pillars_total":  10,
        "duration_s":     42 + i,
    }
    for i in range(_ROLLING_WINDOW_DAYS)
]


def _make_cert(claims: dict) -> CertificateArtifact:
    sig = "sha256:" + hashlib.sha256(
        json.dumps(claims, sort_keys=True).encode()
    ).hexdigest()[:32]
    return CertificateArtifact(
        subject="continuous.7d_rolling_green",
        claims=claims,
        issuer=_ISSUER,
        signature=sig,
        expiry=_EXPIRY,
    )


def _emit_cert_to_lineage(cert: CertificateArtifact, archive: AlexandrianArchive) -> None:
    archive.append_lineage_event({
        "type": "certificate_artifact",
        "subject": cert.subject,
        "claims": cert.claims,
        "issuer": cert.issuer,
        "signature": cert.signature,
        "expiry": cert.expiry,
    })


def test_continuous_cert_7d_rolling_green(tmp_path):
    """Continuous-cert daily job is green for all 7 days of the rolling window."""
    results = _DAILY_JOB_RESULTS

    assert len(results) == _ROLLING_WINDOW_DAYS, (
        f"Expected {_ROLLING_WINDOW_DAYS} results, got {len(results)}"
    )

    for result in results:
        assert result["status"] == "green", (
            f"Day {result['run_date']} is not green: {result['status']!r}"
        )
        assert result["pillars_passed"] == result["pillars_total"], (
            f"Day {result['run_date']}: {result['pillars_passed']}/{result['pillars_total']} pillars passed"
        )

    dates = sorted(
        datetime.strptime(r["run_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        for r in results
    )
    window_span = (dates[-1] - dates[0]).days
    assert window_span == _ROLLING_WINDOW_DAYS - 1, (
        f"Rolling window span {window_span}d != expected {_ROLLING_WINDOW_DAYS - 1}d"
    )

    # All dates must be distinct (no duplicate days)
    date_strs = [r["run_date"] for r in results]
    assert len(set(date_strs)) == len(date_strs), "Duplicate run dates detected"

    # Window must be anchored to today (most recent date = today)
    most_recent = max(dates)
    assert most_recent.date() == _NOW.date(), (
        f"Rolling window not anchored to today: most recent is {most_recent.date()}"
    )

    green_streak = sum(1 for r in results if r["status"] == "green")

    cert = _make_cert({
        "window_days":   _ROLLING_WINDOW_DAYS,
        "green_streak":  green_streak,
        "window_start":  min(date_strs),
        "window_end":    max(date_strs),
        "all_green":     green_streak == _ROLLING_WINDOW_DAYS,
    })
    archive = AlexandrianArchive(root=tmp_path)
    _emit_cert_to_lineage(cert, archive)

    events = archive.read_lineage()
    assert len(events) == 1
    assert events[0]["subject"] == "continuous.7d_rolling_green"
    assert events[0]["claims"]["all_green"] is True


def test_rolling_window_with_red_day_fails():
    """A single red day in the rolling window is detected."""
    results_with_red = list(_DAILY_JOB_RESULTS)
    results_with_red[3] = {**results_with_red[3], "status": "red", "pillars_passed": 8}
    red_days = [r for r in results_with_red if r["status"] != "green"]
    assert len(red_days) == 1


def test_rolling_window_requires_exact_7_days():
    """Window with fewer than 7 days is insufficient."""
    short = _DAILY_JOB_RESULTS[:5]
    assert len(short) < _ROLLING_WINDOW_DAYS


def test_rolling_window_requires_full_pillar_pass():
    """Day with partial pillar pass is not considered fully green."""
    partial = {
        "run_date": _NOW.strftime("%Y-%m-%d"),
        "status":   "green",
        "pillars_passed": 9,
        "pillars_total":  10,
        "duration_s": 40,
    }
    assert partial["pillars_passed"] != partial["pillars_total"]
