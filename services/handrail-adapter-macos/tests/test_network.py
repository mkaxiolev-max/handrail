"""
Tests for network.* namespace handlers.
All network I/O is monkeypatched — no live connections required.
"""
from __future__ import annotations
import asyncio, socket
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from adapter_core.contract import AdapterRequest, OperationStatus
from network_driver.handlers import (
    network_http_get,
    network_port_check,
    network_dns_resolve,
    build_network_handlers,
)


def _req(method: str, **params) -> AdapterRequest:
    return AdapterRequest(method=method, params=params)


# ── network.http_get ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_http_get_success():
    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.status = 200
    mock_resp.headers = {"Content-Type": "text/html"}
    mock_resp.read = MagicMock(return_value=b"<html>hello</html>")

    with patch("urllib.request.urlopen", return_value=mock_resp):
        resp = await network_http_get(_req("network.http_get", url="http://example.com"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["status_code"] == 200
    assert resp.data["url"] == "http://example.com"
    assert "hello" in resp.data["body_preview"]
    assert resp.data["size_bytes"] == len(b"<html>hello</html>")
    assert resp.state_hash.startswith("sha256:")


@pytest.mark.asyncio
async def test_http_get_missing_url():
    resp = await network_http_get(_req("network.http_get"))
    assert resp.status == OperationStatus.FAILURE
    assert "params.url required" in resp.error


@pytest.mark.asyncio
async def test_http_get_http_error():
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
        "http://x.com", 404, "Not Found", {}, None
    )):
        resp = await network_http_get(_req("network.http_get", url="http://x.com"))
    assert resp.status == OperationStatus.FAILURE
    assert "HTTP_ERROR" in resp.error
    assert "404" in resp.error


@pytest.mark.asyncio
async def test_http_get_url_error():
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("nodns")):
        resp = await network_http_get(_req("network.http_get", url="http://bad.invalid"))
    assert resp.status == OperationStatus.FAILURE
    assert "URL_ERROR" in resp.error


# ── network.port_check ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_port_check_open():
    mock_writer = MagicMock()
    mock_writer.close = MagicMock()
    mock_writer.wait_closed = AsyncMock()

    with patch("asyncio.open_connection", new_callable=AsyncMock,
               return_value=(MagicMock(), mock_writer)):
        resp = await network_port_check(_req("network.port_check", host="localhost", port=80))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["open"] is True
    assert resp.data["host"] == "localhost"
    assert resp.data["port"] == 80
    assert resp.data["latency_ms"] >= 0


@pytest.mark.asyncio
async def test_port_check_closed():
    with patch("asyncio.open_connection", side_effect=ConnectionRefusedError):
        resp = await network_port_check(_req("network.port_check", host="localhost", port=9999))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["open"] is False


@pytest.mark.asyncio
async def test_port_check_timeout():
    with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
        resp = await network_port_check(
            _req("network.port_check", host="10.255.255.1", port=80, timeout=0.01)
        )
    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["open"] is False


@pytest.mark.asyncio
async def test_port_check_missing_host():
    resp = await network_port_check(_req("network.port_check", port=80))
    assert resp.status == OperationStatus.FAILURE
    assert "params.host required" in resp.error


@pytest.mark.asyncio
async def test_port_check_missing_port():
    resp = await network_port_check(_req("network.port_check", host="localhost"))
    assert resp.status == OperationStatus.FAILURE
    assert "params.port required" in resp.error


# ── network.dns_resolve ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_dns_resolve_success():
    fake_results = [
        (socket.AF_INET,  socket.SOCK_STREAM, 0, "", ("1.2.3.4", 0)),
        (socket.AF_INET6, socket.SOCK_STREAM, 0, "", ("::1", 0, 0, 0)),
        (socket.AF_INET,  socket.SOCK_STREAM, 0, "", ("1.2.3.4", 0)),  # duplicate, should dedup
    ]
    with patch("socket.getaddrinfo", return_value=fake_results):
        resp = await network_dns_resolve(_req("network.dns_resolve", hostname="example.com"))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["hostname"] == "example.com"
    addrs = resp.data["addresses"]
    assert len(addrs) == 2  # deduplicated
    ips = {a["ip"] for a in addrs}
    assert "1.2.3.4" in ips
    assert "::1" in ips
    families = {a["family"] for a in addrs}
    assert "ipv4" in families
    assert "ipv6" in families


@pytest.mark.asyncio
async def test_dns_resolve_nxdomain():
    with patch("socket.getaddrinfo", side_effect=socket.gaierror("Name not found")):
        resp = await network_dns_resolve(_req("network.dns_resolve", hostname="no.such.host.invalid"))
    assert resp.status == OperationStatus.FAILURE
    assert "DNS_RESOLVE_FAILED" in resp.error


@pytest.mark.asyncio
async def test_dns_resolve_missing_hostname():
    resp = await network_dns_resolve(_req("network.dns_resolve"))
    assert resp.status == OperationStatus.FAILURE
    assert "params.hostname required" in resp.error


# ── registry ─────────────────────────────────────────────────────────────────

def test_build_network_handlers_keys():
    handlers = build_network_handlers()
    assert set(handlers.keys()) == {
        "network.http_get",
        "network.port_check",
        "network.dns_resolve",
    }
    for fn in handlers.values():
        assert callable(fn)
