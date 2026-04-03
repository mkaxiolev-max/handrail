"""
notify.* namespace
==================
macOS notifications and dock badge via AppleScript.

Ops:
  notify.send  — {ok: bool, delivered: bool}
  notify.badge — {ok: bool}

Graceful skip on non-macOS.
"""
from __future__ import annotations
import asyncio, platform
from adapter_core.contract import AdapterRequest, AdapterResponse

IS_MACOS = platform.system() == "Darwin"


async def _osascript(expr: str, timeout: float = 5.0) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        "osascript", "-e", expr,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, stdout.decode().strip(), stderr.decode().strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "", "TIMEOUT"


async def notify_send(req: AdapterRequest) -> AdapterResponse:
    message: str = req.params.get("message", "")
    title: str   = req.params.get("title", "NS∞")

    if not message:
        return AdapterResponse.failure(req, "params.message required")

    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "delivered": False, "skipped": True, "reason": "not_macos"})

    # Escape for AppleScript string literals
    safe_msg   = message.replace('\\', '\\\\').replace('"', '\\"')
    safe_title = title.replace('\\', '\\\\').replace('"', '\\"')
    script = f'display notification "{safe_msg}" with title "{safe_title}"'

    rc, _, err = await _osascript(script)
    if rc != 0:
        return AdapterResponse.failure(req, f"osascript error: {err}")

    return AdapterResponse.success(req, {"ok": True, "delivered": True})


async def notify_badge(req: AdapterRequest) -> AdapterResponse:
    count_raw = req.params.get("count", 0)
    try:
        count = int(count_raw)
    except (TypeError, ValueError):
        return AdapterResponse.failure(req, "params.count must be an integer")

    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "skipped": True, "reason": "not_macos"})

    script = f'set badge of dock tile of current application to {count}'
    rc, _, err = await _osascript(script)
    if rc != 0:
        return AdapterResponse.failure(req, f"osascript error: {err}")

    return AdapterResponse.success(req, {"ok": True})


def build_notify_handlers() -> dict:
    return {
        "notify.send":  notify_send,
        "notify.badge": notify_badge,
    }
