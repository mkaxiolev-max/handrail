"""Tests for speech.* namespace."""
from __future__ import annotations
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from adapter_core.contract import AdapterRequest, OperationStatus
from speech_driver.handlers import speech_say, speech_say_async, speech_voices, speech_stop

def req(params=None):
    return AdapterRequest(method="POST", params=params or {})

@pytest.mark.asyncio
async def test_say_no_text():
    r = await speech_say(req({}))
    assert r.status == OperationStatus.FAILURE

@pytest.mark.asyncio
async def test_say_mock():
    with patch("speech_driver.handlers.IS_MACOS", False):
        r = await speech_say(req({"text": "Hello NS"}))
    assert r.data["said"] == "Hello NS"

@pytest.mark.asyncio
async def test_say_live():
    with patch("speech_driver.handlers.IS_MACOS", True), \
         patch("speech_driver.handlers._run", new=AsyncMock(return_value=(0, "", ""))):
        r = await speech_say(req({"text": "Hello", "voice": "Alex", "rate": 200}))
    assert r.data["ok"] is True

@pytest.mark.asyncio
async def test_say_rate_clamped():
    with patch("speech_driver.handlers.IS_MACOS", False):
        r = await speech_say(req({"text": "hi", "rate": 9999}))
    assert r.data["ok"] is True

@pytest.mark.asyncio
async def test_say_async_mock():
    with patch("speech_driver.handlers.IS_MACOS", False):
        r = await speech_say_async(req({"text": "Hello"}))
    assert r.data["queued"] is True

@pytest.mark.asyncio
async def test_say_async_live():
    mock_proc = MagicMock()
    with patch("speech_driver.handlers.IS_MACOS", True), \
         patch("speech_driver.handlers.subprocess.Popen", return_value=mock_proc):
        r = await speech_say_async(req({"text": "Hello"}))
    assert r.data["queued"] is True

@pytest.mark.asyncio
async def test_voices_mock():
    with patch("speech_driver.handlers.IS_MACOS", False):
        r = await speech_voices(req())
    assert r.data["ok"] is True

@pytest.mark.asyncio
async def test_voices_live():
    voices_out = "Alex     en_US    # Hello\nSamantha en_US    # Hi"
    with patch("speech_driver.handlers.IS_MACOS", True), \
         patch("speech_driver.handlers._run", new=AsyncMock(return_value=(0, voices_out, ""))):
        r = await speech_voices(req())
    assert r.data["count"] >= 1

@pytest.mark.asyncio
async def test_stop_mock():
    with patch("speech_driver.handlers.IS_MACOS", False):
        r = await speech_stop(req())
    assert r.data["stopped"] is True
