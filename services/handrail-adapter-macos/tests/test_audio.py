"""
Tests for audio.* namespace handlers.
All subprocess/osascript calls are monkeypatched — no real audio hardware required.
"""
from __future__ import annotations
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import pytest

from adapter_core.contract import AdapterRequest, OperationStatus
from audio_driver.handlers import (
    audio_get_volume,
    audio_set_volume,
    audio_get_playing,
    build_audio_handlers,
)


def _req(method: str, **params) -> AdapterRequest:
    return AdapterRequest(method=method, params=params)


# ── audio.get_volume ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_volume_macos():
    with patch("audio_driver.handlers.IS_MACOS", True), \
         patch("audio_driver.handlers._osascript", new_callable=AsyncMock) as mock_osa:
        mock_osa.side_effect = [(0, "72", ""), (0, "false", "")]
        resp = await audio_get_volume(_req("audio.get_volume"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["volume"] == 72.0
    assert resp.data["muted"] is False


@pytest.mark.asyncio
async def test_get_volume_muted():
    with patch("audio_driver.handlers.IS_MACOS", True), \
         patch("audio_driver.handlers._osascript", new_callable=AsyncMock) as mock_osa:
        mock_osa.side_effect = [(0, "0", ""), (0, "true", "")]
        resp = await audio_get_volume(_req("audio.get_volume"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["volume"] == 0.0
    assert resp.data["muted"] is True


@pytest.mark.asyncio
async def test_get_volume_non_macos():
    with patch("audio_driver.handlers.IS_MACOS", False):
        resp = await audio_get_volume(_req("audio.get_volume"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["skipped"] is True
    assert resp.data["reason"] == "not_macos"


@pytest.mark.asyncio
async def test_get_volume_osascript_error():
    with patch("audio_driver.handlers.IS_MACOS", True), \
         patch("audio_driver.handlers._osascript", new_callable=AsyncMock) as mock_osa:
        mock_osa.return_value = (1, "", "execution error")
        resp = await audio_get_volume(_req("audio.get_volume"))

    assert resp.status == OperationStatus.FAILURE
    assert "osascript error" in resp.error


# ── audio.set_volume ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_set_volume_success():
    with patch("audio_driver.handlers.IS_MACOS", True), \
         patch("audio_driver.handlers._osascript", new_callable=AsyncMock) as mock_osa:
        mock_osa.return_value = (0, "", "")
        resp = await audio_set_volume(_req("audio.set_volume", volume=50))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["ok"] is True
    assert resp.data["volume_set"] == 50.0


@pytest.mark.asyncio
async def test_set_volume_non_macos():
    with patch("audio_driver.handlers.IS_MACOS", False):
        resp = await audio_set_volume(_req("audio.set_volume", volume=30))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["skipped"] is True
    assert resp.data["volume_set"] == 30.0


@pytest.mark.asyncio
async def test_set_volume_dignity_guard_over():
    with pytest.raises(PermissionError, match="out of allowed range"):
        await audio_set_volume(_req("audio.set_volume", volume=101))


@pytest.mark.asyncio
async def test_set_volume_dignity_guard_under():
    with pytest.raises(PermissionError, match="out of allowed range"):
        await audio_set_volume(_req("audio.set_volume", volume=-1))


@pytest.mark.asyncio
async def test_set_volume_missing_param():
    resp = await audio_set_volume(_req("audio.set_volume"))
    assert resp.status == OperationStatus.FAILURE
    assert "params.volume required" in resp.error


@pytest.mark.asyncio
async def test_set_volume_boundary_zero():
    with patch("audio_driver.handlers.IS_MACOS", True), \
         patch("audio_driver.handlers._osascript", new_callable=AsyncMock) as mock_osa:
        mock_osa.return_value = (0, "", "")
        resp = await audio_set_volume(_req("audio.set_volume", volume=0))
    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["volume_set"] == 0.0


@pytest.mark.asyncio
async def test_set_volume_boundary_hundred():
    with patch("audio_driver.handlers.IS_MACOS", True), \
         patch("audio_driver.handlers._osascript", new_callable=AsyncMock) as mock_osa:
        mock_osa.return_value = (0, "", "")
        resp = await audio_set_volume(_req("audio.set_volume", volume=100))
    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["volume_set"] == 100.0


# ── audio.get_playing ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_playing_music_playing():
    with patch("audio_driver.handlers.IS_MACOS", True), \
         patch("audio_driver.handlers._osascript", new_callable=AsyncMock) as mock_osa:
        mock_osa.side_effect = [(0, "playing", ""), (0, "Bohemian Rhapsody", "")]
        resp = await audio_get_playing(_req("audio.get_playing"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["playing"] is True
    assert resp.data["track"] == "Bohemian Rhapsody"
    assert resp.data["app"] == "Music"


@pytest.mark.asyncio
async def test_get_playing_music_paused():
    with patch("audio_driver.handlers.IS_MACOS", True), \
         patch("audio_driver.handlers._osascript", new_callable=AsyncMock) as mock_osa:
        mock_osa.return_value = (0, "paused", "")
        resp = await audio_get_playing(_req("audio.get_playing"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["playing"] is False
    assert resp.data["track"] == ""


@pytest.mark.asyncio
async def test_get_playing_music_not_running():
    with patch("audio_driver.handlers.IS_MACOS", True), \
         patch("audio_driver.handlers._osascript", new_callable=AsyncMock) as mock_osa:
        mock_osa.return_value = (1, "", "execution error: Music got an error")
        resp = await audio_get_playing(_req("audio.get_playing"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["skipped"] is True
    assert resp.data["reason"] == "music_not_running"


@pytest.mark.asyncio
async def test_get_playing_non_macos():
    with patch("audio_driver.handlers.IS_MACOS", False):
        resp = await audio_get_playing(_req("audio.get_playing"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["skipped"] is True
    assert resp.data["reason"] == "not_macos"


# ── registry ──────────────────────────────────────────────────────────────────

def test_build_audio_handlers_keys():
    handlers = build_audio_handlers()
    assert set(handlers.keys()) == {"audio.get_volume", "audio.set_volume", "audio.get_playing"}
    for fn in handlers.values():
        assert callable(fn)
