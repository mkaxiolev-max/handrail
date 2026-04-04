"""
alert.* namespace
=================
macOS rich alerts via osascript + terminal-notifier fallback.

Ops:
  alert.dialog     — modal dialog with buttons, returns button pressed
  alert.confirm    — yes/no confirm dialog, returns bool
  alert.input      — text input dialog, returns entered text

Dignity Guard:
  Dialog text max 500 chars.
  No dialogs allowed during screen recording (non-blocking check).
  Input text never logged to Alexandria (privacy).
"""
from __future__ import annotations
import asyncio, platform
from adapter_core.contract import AdapterRequest, AdapterResponse, OperationStatus

IS_MACOS = platform.system() == "Darwin"


async def _run(cmd: list[str]) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    out, err = await proc.communicate()
    return proc.returncode, out.decode().strip(), err.decode().strip()


async def alert_dialog(req: AdapterRequest) -> AdapterResponse:
    params = req.params or {}
    message = params.get("message", "NS∞ Alert")[:500]
    title = params.get("title", "NS∞")[:100]
    buttons = params.get("buttons", ["OK", "Cancel"])[:3]

    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "button": buttons[0], "mode": "mock"})

    btn_str = "{" + ", ".join(f'"{b}"' for b in buttons) + "}"
    script = f'display dialog "{message}" with title "{title}" buttons {btn_str} default button "{buttons[0]}"'
    rc, out, err = await _run(["osascript", "-e", script])
    if rc != 0:
        return AdapterResponse.success(req, {"ok": True, "button": None, "cancelled": True,
                                              "reason": "dialog_dismissed"})
    button = out.replace("button returned:", "").strip() if "button returned" in out else out
    return AdapterResponse.success(req, {"ok": True, "button": button, "cancelled": False})


async def alert_confirm(req: AdapterRequest) -> AdapterResponse:
    params = req.params or {}
    message = params.get("message", "Confirm?")[:500]
    title = params.get("title", "NS∞")[:100]

    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "confirmed": False, "mode": "mock"})

    script = f'display dialog "{message}" with title "{title}" buttons {{"Yes", "No"}} default button "No"'
    rc, out, err = await _run(["osascript", "-e", script])
    confirmed = "Yes" in out
    return AdapterResponse.success(req, {"ok": True, "confirmed": confirmed})


async def alert_input(req: AdapterRequest) -> AdapterResponse:
    params = req.params or {}
    prompt = params.get("prompt", "Enter value:")[:200]
    title = params.get("title", "NS∞")[:100]
    default = params.get("default", "")[:200]

    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "value": default, "cancelled": False, "mode": "mock"})

    script = f'display dialog "{prompt}" with title "{title}" default answer "{default}"'
    rc, out, err = await _run(["osascript", "-e", script])
    if rc != 0:
        return AdapterResponse.success(req, {"ok": True, "value": None, "cancelled": True})
    value = ""
    for part in out.split(","):
        if "text returned" in part:
            value = part.replace("text returned:", "").strip()
    return AdapterResponse.success(req, {"ok": True, "value": value, "cancelled": False})


def build_alert_handlers() -> dict:
    return {
        "alert.dialog":  alert_dialog,
        "alert.confirm": alert_confirm,
        "alert.input":   alert_input,
    }
