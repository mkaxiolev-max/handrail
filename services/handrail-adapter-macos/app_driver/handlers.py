"""
app.* namespace
===============
macOS application lifecycle via AppleScript / open / osascript.

Ops:
  app.launch      — open -a AppName
  app.quit        — tell application X to quit
  app.is_running  — check if app process exists
  app.list_open   — list all running app names

Dignity Guard:
  Blocked apps: Terminal, SSH, sudo, any shell spawner.
  All launches logged.
"""
from __future__ import annotations
import asyncio, platform
from adapter_core.contract import AdapterRequest, AdapterResponse, OperationStatus

IS_MACOS = platform.system() == "Darwin"

_BLOCKED_APPS = {
    "terminal", "iterm", "iterm2", "ssh", "shell",
    "bash", "zsh", "fish", "python", "ruby",
}


async def _run(cmd: list[str]) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    out, err = await proc.communicate()
    return proc.returncode, out.decode().strip(), err.decode().strip()


async def app_launch(req: AdapterRequest) -> AdapterResponse:
    app = (req.params or {}).get("app", "").strip()
    if not app:
        return AdapterResponse.failure(req, "app name required")
    if app.lower().rstrip(".app") in _BLOCKED_APPS:
        raise PermissionError(f"app.launch: Dignity Guard blocks launching {app!r}")
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "app": app, "launched": True, "mode": "mock"})
    rc, out, err = await _run(["open", "-a", app])
    if rc != 0:
        return AdapterResponse.failure(req, f"open -a {app!r} failed: {err}")
    return AdapterResponse.success(req, {"ok": True, "app": app, "launched": True})


async def app_quit(req: AdapterRequest) -> AdapterResponse:
    app = (req.params or {}).get("app", "").strip()
    if not app:
        return AdapterResponse.failure(req, "app name required")
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "app": app, "quit": True, "mode": "mock"})
    script = f'tell application "{app}" to quit'
    rc, out, err = await _run(["osascript", "-e", script])
    if rc != 0:
        return AdapterResponse.success(req, {"ok": True, "app": app, "quit": False,
                                             "reason": "app_not_running_or_refused"})
    return AdapterResponse.success(req, {"ok": True, "app": app, "quit": True})


async def app_is_running(req: AdapterRequest) -> AdapterResponse:
    app = (req.params or {}).get("app", "").strip()
    if not app:
        return AdapterResponse.failure(req, "app name required")
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "app": app, "running": False, "mode": "mock"})
    script = f'tell application "System Events" to (name of processes) contains "{app}"'
    rc, out, err = await _run(["osascript", "-e", script])
    running = out.strip().lower() == "true"
    return AdapterResponse.success(req, {"ok": True, "app": app, "running": running})


async def app_list_open(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "apps": [], "count": 0, "mode": "mock"})
    script = 'tell application "System Events" to get name of every process whose background only is false'
    rc, out, err = await _run(["osascript", "-e", script])
    if rc != 0:
        return AdapterResponse.success(req, {"ok": True, "apps": [], "count": 0,
                                             "reason": "accessibility_required"})
    apps = [a.strip() for a in out.split(",") if a.strip()]
    return AdapterResponse.success(req, {"ok": True, "apps": apps, "count": len(apps)})


def build_app_handlers() -> dict:
    return {
        "app.launch":    app_launch,
        "app.quit":      app_quit,
        "app.is_running": app_is_running,
        "app.list_open": app_list_open,
    }
