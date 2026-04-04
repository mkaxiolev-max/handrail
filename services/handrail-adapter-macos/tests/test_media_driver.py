"""Tests for media.* namespace."""
from __future__ import annotations
from unittest.mock import AsyncMock, patch
import pytest
from adapter_core.contract import AdapterRequest, OperationStatus
from media_driver.handlers import media_now_playing, media_play_pause, media_next, media_volume

def req(params=None):
    return AdapterRequest(method="POST", params=params or {})

@pytest.mark.asyncio
async def test_now_playing_mock():
    with patch("media_driver.handlers.IS_MACOS", False):
        r = await media_now_playing(req())
    assert r.data["ok"] is True

@pytest.mark.asyncio
async def test_now_playing_live():
    with patch("media_driver.handlers.IS_MACOS", True), \
         patch("media_driver.handlers._run", new=AsyncMock(return_value=(0, "Bohemian Rhapsody|Queen|A Night at the Opera", ""))):
        r = await media_now_playing(req())
    assert r.data["playing"] is True
    assert r.data["track"] == "Bohemian Rhapsody"

@pytest.mark.asyncio
async def test_now_playing_none():
    with patch("media_driver.handlers.IS_MACOS", True), \
         patch("media_driver.handlers._run", new=AsyncMock(return_value=(1, "", "not playing"))):
        r = await media_now_playing(req())
    assert r.data["playing"] is False

@pytest.mark.asyncio
async def test_play_pause_mock():
    with patch("media_driver.handlers.IS_MACOS", False):
        r = await media_play_pause(req())
    assert r.data["toggled"] is True

@pytest.mark.asyncio
async def test_next_mock():
    with patch("media_driver.handlers.IS_MACOS", False):
        r = await media_next(req())
    assert r.data["skipped"] is True

@pytest.mark.asyncio
async def test_volume_get_mock():
    with patch("media_driver.handlers.IS_MACOS", False):
        r = await media_volume(req())
    assert r.data["volume"] == 50
    assert r.data["action"] == "get"

@pytest.mark.asyncio
async def test_volume_set_mock():
    with patch("media_driver.handlers.IS_MACOS", False):
        r = await media_volume(req({"volume": 75}))
    assert r.data["volume"] == 75
    assert r.data["action"] == "set"
