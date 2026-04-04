"""Tests for alert.* namespace."""
from __future__ import annotations
from unittest.mock import AsyncMock, patch
import pytest
from adapter_core.contract import AdapterRequest, OperationStatus
from alert_driver.handlers import alert_dialog, alert_confirm, alert_input

def req(params=None):
    return AdapterRequest(method="POST", params=params or {})

@pytest.mark.asyncio
async def test_dialog_mock():
    with patch("alert_driver.handlers.IS_MACOS", False):
        r = await alert_dialog(req({"message": "test", "buttons": ["OK", "Cancel"]}))
    assert r.data["ok"] is True
    assert r.data["button"] == "OK"

@pytest.mark.asyncio
async def test_dialog_live_ok():
    with patch("alert_driver.handlers.IS_MACOS", True), \
         patch("alert_driver.handlers._run", new=AsyncMock(return_value=(0, "button returned:OK", ""))):
        r = await alert_dialog(req({"message": "test"}))
    assert r.data["button"] == "OK"
    assert r.data["cancelled"] is False

@pytest.mark.asyncio
async def test_dialog_cancelled():
    with patch("alert_driver.handlers.IS_MACOS", True), \
         patch("alert_driver.handlers._run", new=AsyncMock(return_value=(1, "", "User cancelled"))):
        r = await alert_dialog(req({"message": "test"}))
    assert r.data["cancelled"] is True

@pytest.mark.asyncio
async def test_confirm_yes():
    with patch("alert_driver.handlers.IS_MACOS", True), \
         patch("alert_driver.handlers._run", new=AsyncMock(return_value=(0, "button returned:Yes", ""))):
        r = await alert_confirm(req({"message": "Are you sure?"}))
    assert r.data["confirmed"] is True

@pytest.mark.asyncio
async def test_confirm_no():
    with patch("alert_driver.handlers.IS_MACOS", True), \
         patch("alert_driver.handlers._run", new=AsyncMock(return_value=(0, "button returned:No", ""))):
        r = await alert_confirm(req({"message": "Are you sure?"}))
    assert r.data["confirmed"] is False

@pytest.mark.asyncio
async def test_input_mock():
    with patch("alert_driver.handlers.IS_MACOS", False):
        r = await alert_input(req({"prompt": "Enter:", "default": "hello"}))
    assert r.data["value"] == "hello"

@pytest.mark.asyncio
async def test_input_live():
    with patch("alert_driver.handlers.IS_MACOS", True), \
         patch("alert_driver.handlers._run", new=AsyncMock(return_value=(0, "text returned:myvalue, button returned:OK", ""))):
        r = await alert_input(req({"prompt": "Enter:"}))
    assert r.data["value"] == "myvalue"
    assert r.data["cancelled"] is False

@pytest.mark.asyncio
async def test_input_cancelled():
    with patch("alert_driver.handlers.IS_MACOS", True), \
         patch("alert_driver.handlers._run", new=AsyncMock(return_value=(1, "", "cancelled"))):
        r = await alert_input(req({"prompt": "Enter:"}))
    assert r.data["cancelled"] is True
