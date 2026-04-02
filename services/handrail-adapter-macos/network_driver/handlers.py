"""
network.* namespace
===================
HTTP, port reachability, DNS resolution — all read-only, stdlib-only.

Methods:
  network.http_get      — HTTP GET, returns status + body preview
  network.port_check    — TCP connect probe, returns open/closed + latency
  network.dns_resolve   — DNS A/AAAA lookup, returns address list

Contract: every handler returns AdapterResponse.
Dignity Kernel pre-check is enforced by server.py before dispatch.
"""
from __future__ import annotations
import asyncio, socket, time, urllib.error, urllib.request
from typing import Any

from adapter_core.contract import AdapterRequest, AdapterResponse

# Max bytes read from HTTP response body (preview only)
_BODY_PREVIEW_BYTES = 4096
_BODY_PREVIEW_CHARS = 512


async def network_http_get(req: AdapterRequest) -> AdapterResponse:
    url: str = req.params.get("url", "")
    if not url:
        return AdapterResponse.failure(req, "params.url required")

    timeout: int = int(req.params.get("timeout", 10))
    extra_headers: dict[str, str] = req.params.get("headers", {})

    http_req = urllib.request.Request(url, headers=extra_headers)

    def _fetch() -> tuple[int, dict[str, Any], bytes]:
        with urllib.request.urlopen(http_req, timeout=timeout) as resp:
            body = resp.read(_BODY_PREVIEW_BYTES)
            return resp.status, dict(resp.headers), body

    loop = asyncio.get_event_loop()
    try:
        status_code, resp_headers, body = await loop.run_in_executor(None, _fetch)
    except urllib.error.HTTPError as exc:
        return AdapterResponse.failure(req, f"HTTP_ERROR: {exc.code} {exc.reason}")
    except urllib.error.URLError as exc:
        return AdapterResponse.failure(req, f"URL_ERROR: {exc.reason}")
    except Exception as exc:
        return AdapterResponse.failure(req, f"REQUEST_FAILED: {type(exc).__name__}: {exc}")

    body_preview = body.decode("utf-8", errors="replace")[:_BODY_PREVIEW_CHARS]
    return AdapterResponse.success(req, {
        "url": url,
        "status_code": status_code,
        "content_type": resp_headers.get("Content-Type", ""),
        "body_preview": body_preview,
        "size_bytes": len(body),
    })


async def network_port_check(req: AdapterRequest) -> AdapterResponse:
    host: str = req.params.get("host", "")
    port_raw = req.params.get("port")
    if not host:
        return AdapterResponse.failure(req, "params.host required")
    if port_raw is None:
        return AdapterResponse.failure(req, "params.port required")

    port = int(port_raw)
    timeout: float = float(req.params.get("timeout", 3.0))

    t0 = time.monotonic()
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=timeout
        )
        latency_ms = int((time.monotonic() - t0) * 1000)
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return AdapterResponse.success(req, {
            "host": host, "port": port, "open": True, "latency_ms": latency_ms,
        })
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        latency_ms = int((time.monotonic() - t0) * 1000)
        return AdapterResponse.success(req, {
            "host": host, "port": port, "open": False, "latency_ms": latency_ms,
        })


async def network_dns_resolve(req: AdapterRequest) -> AdapterResponse:
    hostname: str = req.params.get("hostname", "")
    if not hostname:
        return AdapterResponse.failure(req, "params.hostname required")

    def _resolve() -> list[tuple]:
        return socket.getaddrinfo(hostname, None)

    loop = asyncio.get_event_loop()
    try:
        results = await loop.run_in_executor(None, _resolve)
    except socket.gaierror as exc:
        return AdapterResponse.failure(req, f"DNS_RESOLVE_FAILED: {exc}")
    except Exception as exc:
        return AdapterResponse.failure(req, f"DNS_ERROR: {type(exc).__name__}: {exc}")

    addresses: list[dict] = []
    seen: set[str] = set()
    for family, _, _, _, sockaddr in results:
        ip: str = sockaddr[0]
        if ip in seen:
            continue
        seen.add(ip)
        addresses.append({
            "ip": ip,
            "family": "ipv6" if family == socket.AF_INET6 else "ipv4",
        })

    return AdapterResponse.success(req, {"hostname": hostname, "addresses": addresses})


def build_network_handlers() -> dict:
    return {
        "network.http_get":    network_http_get,
        "network.port_check":  network_port_check,
        "network.dns_resolve": network_dns_resolve,
    }
