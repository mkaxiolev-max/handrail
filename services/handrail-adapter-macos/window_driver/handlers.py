"""
window.* namespace
==================
macOS window management via AppleScript + System Events.

Ops:
  window.list        — [{app, title, minimized}] for all foreground processes
  window.focus       — activate named application
  window.get_focused — {app, title} of frontmost process

Dignity Guard:
  All ops gracefully skip on -1719 (Accessibility not granted).
  window.list returns empty list (not failure) on permission denial.
"""
from __future__ import annotations
import asyncio, platform
from adapter_core.contract import AdapterRequest, AdapterResponse

IS_MACOS = platform.system() == "Darwin"


async def _run(cmd: list[str], timeout: float = 5.0) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode().strip(), err.decode().strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "", "TIMEOUT"


def _is_accessibility_error(err: str) -> bool:
    return "-1719" in err or "assistive" in err.lower()


_LIST_SCRIPT = '''tell application "System Events"
  set appList to {}
  repeat with p in (every process whose background only is false)
    set end of appList to name of p
  end repeat
  return appList
end tell'''


async def window_list(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {"skipped": True, "reason": "not_macos", "windows": [], "count": 0})
    rc, out, err = await _run(["osascript", "-e", _LIST_SCRIPT])
    if rc != 0:
        if _is_accessibility_error(err):
            return AdapterResponse.success(req, {
                "skipped": True, "reason": "accessibility_permission_required",
                "windows": [], "count": 0,
            })
        return AdapterResponse.failure(req, f"window.list failed: {err[:200]}")
    apps = [a.strip() for a in out.split(",") if a.strip()]
    windows = [{"app": a, "title": "", "minimized": False} for a in apps]
    return AdapterResponse.success(req, {"windows": windows, "count": len(windows)})


async def window_focus(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {"skipped": True, "reason": "not_macos"})
    app = (req.params or {}).get("app", "")
    if not app:
        return AdapterResponse.failure(req, "params.app required")
    script = f'tell application "{app}" to activate'
    rc, _, err = await _run(["osascript", "-e", script])
    if rc != 0:
        return AdapterResponse.failure(req, f"focus failed: {err[:200]}")
    return AdapterResponse.success(req, {"ok": True, "focused_app": app})


_FOCUSED_SCRIPT = '''tell application "System Events"
  set fp to first process whose frontmost is true
  set appName to name of fp
  set windowTitle to ""
  try
    set windowTitle to name of front window of fp
  end try
  return appName & "|" & windowTitle
end tell'''


async def window_get_focused(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {"skipped": True, "reason": "not_macos", "app": "", "title": ""})
    rc, out, err = await _run(["osascript", "-e", _FOCUSED_SCRIPT])
    if rc != 0:
        if _is_accessibility_error(err):
            return AdapterResponse.success(req, {
                "app": "", "title": "", "skipped": True,
                "reason": "accessibility_permission_required",
            })
        return AdapterResponse.failure(req, f"get_focused failed: {err[:200]}")
    parts = out.split("|", 1)
    return AdapterResponse.success(req, {
        "app": parts[0].strip(),
        "title": parts[1].strip() if len(parts) > 1 else "",
    })


def build_window_handlers() -> dict:
    return {
        "window.list":        window_list,
        "window.focus":       window_focus,
        "window.get_focused": window_get_focused,
    }
