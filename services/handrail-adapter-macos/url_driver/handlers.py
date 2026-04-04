"""
url.* namespace
===============
macOS URL/browser operations.

Ops:
  url.open       — open URL in default browser (dignity: http/https only)
  url.fetch      — fetch URL content, return first 2000 chars
  url.qr         — generate QR code PNG for URL (base64)

Dignity Guard:
  open: http/https only, no file:// or javascript: schemes
  fetch: timeout 10s, max 2000 chars returned
  qr: URL validated before encoding
"""
from __future__ import annotations
import asyncio, platform, re
from adapter_core.contract import AdapterRequest, AdapterResponse, OperationStatus

IS_MACOS = platform.system() == "Darwin"
_SAFE_URL = re.compile(r'^https?://')


async def _run(cmd: list[str]) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    out, err = await proc.communicate()
    return proc.returncode, out.decode().strip(), err.decode().strip()


async def url_open(req: AdapterRequest) -> AdapterResponse:
    url = (req.params or {}).get("url", "").strip()
    if not url:
        return AdapterResponse.failure(req, "url required")
    if not _SAFE_URL.match(url):
        raise PermissionError(f"url.open: Dignity Guard blocks non-http URL: {url[:60]!r}")
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "url": url, "opened": True, "mode": "mock"})
    rc, out, err = await _run(["open", url])
    if rc != 0:
        return AdapterResponse.failure(req, f"open failed: {err[:60]}")
    return AdapterResponse.success(req, {"ok": True, "url": url, "opened": True})


async def url_fetch(req: AdapterRequest) -> AdapterResponse:
    url = (req.params or {}).get("url", "").strip()
    max_chars = min(int((req.params or {}).get("max_chars", 2000)), 5000)
    if not url:
        return AdapterResponse.failure(req, "url required")
    if not _SAFE_URL.match(url):
        raise PermissionError(f"url.fetch: Dignity Guard blocks non-http URL")
    try:
        import httpx
        r = httpx.get(url, timeout=10, follow_redirects=True,
                      headers={"User-Agent": "NS-Adapter/1.0"})
        content = r.text[:max_chars]
        return AdapterResponse.success(req, {
            "ok": True, "url": url, "status": r.status_code,
            "content": content, "content_length": len(r.text),
            "truncated": len(r.text) > max_chars
        })
    except Exception as e:
        return AdapterResponse.success(req, {"ok": True, "url": url,
                                              "skipped": True, "reason": str(e)[:80]})


async def url_qr(req: AdapterRequest) -> AdapterResponse:
    url = (req.params or {}).get("url", "").strip()
    if not url:
        return AdapterResponse.failure(req, "url required")
    if not _SAFE_URL.match(url):
        raise PermissionError(f"url.qr: Dignity Guard blocks non-http URL")
    try:
        import qrcode
        import base64
        from io import BytesIO
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        return AdapterResponse.success(req, {"ok": True, "url": url,
                                              "qr_base64": b64, "format": "png"})
    except ImportError:
        return AdapterResponse.success(req, {"ok": True, "url": url,
                                              "skipped": True, "reason": "qrcode_not_installed"})
    except Exception as e:
        return AdapterResponse.success(req, {"ok": True, "skipped": True, "reason": str(e)[:80]})


def build_url_handlers() -> dict:
    return {
        "url.open":  url_open,
        "url.fetch": url_fetch,
        "url.qr":    url_qr,
    }
