"""
Tests for vision.* namespace handlers.
All subprocess calls and file I/O are monkeypatched — no screen access required.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
import pytest

from adapter_core.contract import AdapterRequest, OperationStatus
from vision_driver.handlers import (
    vision_screenshot,
    vision_ocr_region,
    build_vision_handlers,
)


def _req(method: str, **params) -> AdapterRequest:
    return AdapterRequest(method=method, params=params)


# ── vision.screenshot ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_screenshot_mock_mode(tmp_path):
    """Non-macOS path: writes stub PNG and returns mock=True."""
    with patch("vision_driver.handlers.IS_MACOS", False), \
         patch("vision_driver.handlers.ARTIFACTS_ROOT", tmp_path):
        resp = await vision_screenshot(_req("vision.screenshot"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["mock"] is True
    assert resp.data["hash"] == "sha256:mock0000"
    assert len(resp.artifacts) == 1


@pytest.mark.asyncio
async def test_screenshot_live_success(tmp_path):
    """macOS path: screencapture succeeds, returns hash + size."""
    fake_png = b"\x89PNG\r\n\x1a\nFAKE"
    expected_hash = "sha256:" + hashlib.sha256(fake_png).hexdigest()[:16]

    def fake_artifact_path(run_id, name):
        p = tmp_path / run_id
        p.mkdir(parents=True, exist_ok=True)
        return p / name

    with patch("vision_driver.handlers.IS_MACOS", True), \
         patch("vision_driver.handlers._artifact_path", side_effect=fake_artifact_path), \
         patch("vision_driver.handlers._run", new_callable=AsyncMock) as mock_run:

        mock_run.return_value = (0, "", "")
        req = _req("vision.screenshot")
        # Write fake bytes so read_bytes() works
        out_path = fake_artifact_path(req.run_id, "screenshot.png")
        out_path.write_bytes(fake_png)

        resp = await vision_screenshot(req)

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["hash"] == expected_hash
    assert resp.data["size_bytes"] == len(fake_png)
    assert len(resp.artifacts) == 1


@pytest.mark.asyncio
async def test_screenshot_live_failure(tmp_path):
    """screencapture non-zero rc → FAILURE."""
    def fake_artifact_path(run_id, name):
        p = tmp_path / run_id
        p.mkdir(parents=True, exist_ok=True)
        return p / name

    with patch("vision_driver.handlers.IS_MACOS", True), \
         patch("vision_driver.handlers._artifact_path", side_effect=fake_artifact_path), \
         patch("vision_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (1, "", "permission denied")
        resp = await vision_screenshot(_req("vision.screenshot"))

    assert resp.status == OperationStatus.FAILURE
    assert "screencapture failed" in resp.error


@pytest.mark.asyncio
async def test_screenshot_with_region(tmp_path):
    """Region params are forwarded to screencapture -R."""
    fake_png = b"\x89PNG\r\n\x1a\nREGION"

    def fake_artifact_path(run_id, name):
        p = tmp_path / run_id
        p.mkdir(parents=True, exist_ok=True)
        return p / name

    with patch("vision_driver.handlers.IS_MACOS", True), \
         patch("vision_driver.handlers._artifact_path", side_effect=fake_artifact_path), \
         patch("vision_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (0, "", "")
        req = _req("vision.screenshot", x=10, y=20, w=300, h=200)
        out_path = fake_artifact_path(req.run_id, "screenshot.png")
        out_path.write_bytes(fake_png)
        resp = await vision_screenshot(req)

    assert resp.status == OperationStatus.SUCCESS
    # Verify -R was included in the command
    call_args = mock_run.call_args[0][0]
    assert "-R" in call_args
    assert "10,20,300,200" in call_args


# ── vision.ocr_region ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ocr_region_mock_mode(tmp_path):
    with patch("vision_driver.handlers.IS_MACOS", False), \
         patch("vision_driver.handlers.ARTIFACTS_ROOT", tmp_path):
        resp = await vision_ocr_region(_req("vision.ocr_region", x=0, y=0, w=400, h=100))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["mock"] is True
    assert resp.data["text"] == "[MOCK OCR TEXT]"
    assert resp.data["confidence"] == 0.99


@pytest.mark.asyncio
async def test_ocr_region_no_tesseract(tmp_path):
    """tesseract not installed → graceful skip, still SUCCESS."""
    def fake_artifact_path(run_id, name):
        p = tmp_path / run_id
        p.mkdir(parents=True, exist_ok=True)
        return p / name

    with patch("vision_driver.handlers.IS_MACOS", True), \
         patch("vision_driver.handlers._artifact_path", side_effect=fake_artifact_path), \
         patch("vision_driver.handlers._run", new_callable=AsyncMock) as mock_run, \
         patch("vision_driver.handlers.shutil.which", return_value=None):
        mock_run.return_value = (0, "", "")
        resp = await vision_ocr_region(_req("vision.ocr_region", x=0, y=0, w=200, h=50))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["text"] is None
    assert "tesseract not installed" in resp.data["note"]


@pytest.mark.asyncio
async def test_ocr_region_with_tesseract(tmp_path):
    """tesseract installed → run it, return text."""
    def fake_artifact_path(run_id, name):
        p = tmp_path / run_id
        p.mkdir(parents=True, exist_ok=True)
        return p / name

    with patch("vision_driver.handlers.IS_MACOS", True), \
         patch("vision_driver.handlers._artifact_path", side_effect=fake_artifact_path), \
         patch("vision_driver.handlers.shutil.which", return_value="/usr/local/bin/tesseract"), \
         patch("vision_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        # First call: screencapture, second call: tesseract
        mock_run.side_effect = [(0, "", ""), (0, "Hello World", "")]
        resp = await vision_ocr_region(_req("vision.ocr_region", x=0, y=0, w=200, h=50))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["text"] == "Hello World"


@pytest.mark.asyncio
async def test_ocr_region_screencapture_failure(tmp_path):
    def fake_artifact_path(run_id, name):
        p = tmp_path / run_id
        p.mkdir(parents=True, exist_ok=True)
        return p / name

    with patch("vision_driver.handlers.IS_MACOS", True), \
         patch("vision_driver.handlers._artifact_path", side_effect=fake_artifact_path), \
         patch("vision_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (1, "", "no screen recording permission")
        resp = await vision_ocr_region(_req("vision.ocr_region"))

    assert resp.status == OperationStatus.FAILURE
    assert "screencapture failed" in resp.error


@pytest.mark.asyncio
async def test_ocr_region_default_params(tmp_path):
    """Missing params default to x=0, y=0, w=400, h=100."""
    def fake_artifact_path(run_id, name):
        p = tmp_path / run_id
        p.mkdir(parents=True, exist_ok=True)
        return p / name

    with patch("vision_driver.handlers.IS_MACOS", True), \
         patch("vision_driver.handlers._artifact_path", side_effect=fake_artifact_path), \
         patch("vision_driver.handlers.shutil.which", return_value=None), \
         patch("vision_driver.handlers._run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (0, "", "")
        resp = await vision_ocr_region(_req("vision.ocr_region"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["region"] == {"x": 0, "y": 0, "w": 400, "h": 100}


# ── registry ──────────────────────────────────────────────────────────────────

def test_build_vision_handlers_keys():
    handlers = build_vision_handlers()
    assert set(handlers.keys()) == {"vision.screenshot", "vision.ocr_region"}
    for fn in handlers.values():
        assert callable(fn)
