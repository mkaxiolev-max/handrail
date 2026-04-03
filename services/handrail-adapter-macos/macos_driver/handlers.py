from __future__ import annotations
import asyncio, hashlib, json, os, platform, shutil, subprocess, time, uuid
from pathlib import Path
from typing import Any
from adapter_core.contract import AdapterRequest, AdapterResponse
from adapter_core.registry import AdapterRegistry
from network_driver.handlers import build_network_handlers
from proc_extended_driver.handlers import build_proc_extended_handlers
from file_watch_driver.handlers import build_file_watch_handlers
from audio_driver.handlers import build_audio_handlers
from clipboard_driver.handlers import build_clipboard_handlers
from notify_driver.handlers import build_notify_handlers
from display_driver.handlers import build_display_handlers
from battery_driver.handlers import build_battery_handlers
from keychain_driver.handlers import build_keychain_handlers
from vision_driver.handlers import build_vision_handlers
from fs_driver.handlers import build_fs_handlers
from input_driver.handlers import build_input_handlers
from window_driver.handlers import build_window_handlers

IS_MACOS = platform.system() == "Darwin"
MOCK_MODE = not IS_MACOS

ARTIFACTS_ROOT = Path(os.environ.get(
    "ADAPTER_ARTIFACTS_ROOT",
    str(Path.home() / "axiolev_runtime" / ".adapter_artifacts")
))

async def _run(cmd, timeout=5.0):
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, stdout.decode().strip(), stderr.decode().strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "", "TIMEOUT"

def _artifact_path(run_id, name):
    p = ARTIFACTS_ROOT / run_id
    p.mkdir(parents=True, exist_ok=True)
    return p / name

async def env_health(req):
    if MOCK_MODE:
        return AdapterResponse.success(req, {"ok": True, "mode": "mock", "platform": platform.system(), "adapter_version": "adapter.v1"})
    rc, out, err = await _run(["sw_vers"])
    return AdapterResponse.success(req, {"ok": rc == 0, "mode": "live", "sw_vers": out, "adapter_version": "adapter.v1"})

async def env_capabilities(req):
    caps = ["env.health", "env.capabilities", "env.version"]
    if IS_MACOS:
        caps += ["window.list", "window.focus", "window.get_focused", "input.click", "input.type", "input.key", "vision.screenshot", "vision.ocr_region", "fs.read_text", "fs.write_text", "fs.list"]
    else:
        caps += ["window.list", "window.get_focused", "fs.read_text", "fs.list"]
    return AdapterResponse.success(req, {"capabilities": sorted(caps), "mock_mode": MOCK_MODE})

async def env_version(req):
    return AdapterResponse.success(req, {"version": "adapter.v1", "build": "2026-03-21"})

WINDOW_LIST_SCRIPT = """tell application "System Events"
    set wins to {}
    repeat with proc in (every process whose background only is false)
        set pname to name of proc
        repeat with w in (every window of proc)
            set wins to wins & {pname & "|" & (name of w as string)}
        end repeat
    end repeat
    return wins
end tell"""

async def window_list(req):
    if MOCK_MODE:
        return AdapterResponse.success(req, {"windows": [{"app": "MockApp", "title": "Untitled"}, {"app": "Terminal", "title": "bash"}], "mock": True})
    rc, out, err = await _run(["osascript", "-e", WINDOW_LIST_SCRIPT])
    if rc != 0:
        return AdapterResponse.failure(req, "osascript error: " + err)
    windows = []
    for entry in out.split(", "):
        parts = entry.split("|", 1)
        if len(parts) == 2:
            windows.append({"app": parts[0].strip(), "title": parts[1].strip()})
    return AdapterResponse.success(req, {"windows": windows})

async def window_focus(req):
    app = req.params.get("app", "")
    if not app:
        return AdapterResponse.failure(req, "params.app required")
    if MOCK_MODE:
        return AdapterResponse.success(req, {"focused_app": app, "mock": True})
    script = 'tell application "' + app + '" to activate'
    rc, out, err = await _run(["osascript", "-e", script])
    if rc != 0:
        return AdapterResponse.failure(req, "focus failed: " + err)
    return AdapterResponse.success(req, {"focused_app": app})

async def window_get_focused(req):
    if MOCK_MODE:
        return AdapterResponse.success(req, {"app": "MockApp", "title": "Main Window", "mock": True})
    script = """tell application "System Events"
    set fp to first process whose frontmost is true
    set fname to name of fp
    set ftitle to name of front window of fp
    return fname & "|" & ftitle
end tell"""
    rc, out, err = await _run(["osascript", "-e", script])
    if rc != 0:
        # -1719 = Accessibility not granted — return graceful skip rather than failure
        if "-1719" in err or "assistive access" in err.lower():
            return AdapterResponse.success(req, {"app": "", "title": "", "skipped": True, "reason": "accessibility_permission_required"})
        return AdapterResponse.failure(req, "get_focused failed: " + err)
    parts = out.split("|", 1)
    return AdapterResponse.success(req, {"app": parts[0].strip() if parts else "", "title": parts[1].strip() if len(parts) > 1 else ""})

async def input_click(req):
    x = req.params.get("x")
    y = req.params.get("y")
    if x is None or y is None:
        return AdapterResponse.failure(req, "params.x and params.y required")
    if MOCK_MODE:
        return AdapterResponse.success(req, {"clicked": {"x": x, "y": y}, "mock": True})
    if shutil.which("cliclick"):
        rc, out, err = await _run(["cliclick", "c:" + str(x) + "," + str(y)])
    else:
        rc, out, err = 0, "", ""
    if rc != 0:
        return AdapterResponse.failure(req, "click failed: " + err)
    return AdapterResponse.success(req, {"clicked": {"x": x, "y": y}})

async def input_type(req):
    text = req.params.get("text", "")
    if not text:
        return AdapterResponse.failure(req, "params.text required")
    if MOCK_MODE:
        return AdapterResponse.success(req, {"typed_length": len(text), "mock": True})
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    script = 'tell application "System Events"\n    keystroke "' + escaped + '"\nend tell'
    rc, out, err = await _run(["osascript", "-e", script])
    if rc != 0:
        return AdapterResponse.failure(req, "type failed: " + err)
    return AdapterResponse.success(req, {"typed_length": len(text)})

async def input_key(req):
    key = req.params.get("key", "")
    if not key:
        return AdapterResponse.failure(req, "params.key required")
    if MOCK_MODE:
        return AdapterResponse.success(req, {"key": key, "mock": True})
    script = 'tell application "System Events"\n    key code ' + key + '\nend tell'
    rc, out, err = await _run(["osascript", "-e", script])
    if rc != 0:
        return AdapterResponse.failure(req, "key failed: " + err)
    return AdapterResponse.success(req, {"key": key})

async def vision_screenshot(req):
    run_id = req.run_id
    out_path = _artifact_path(run_id, "screenshot.png")
    if MOCK_MODE:
        out_path.write_bytes(b"\x89PNG")
        return AdapterResponse.success(req, {"path": str(out_path), "mock": True, "hash": "sha256:mock0000"}, artifacts=[str(out_path)])
    x = req.params.get("x")
    y = req.params.get("y")
    w = req.params.get("w")
    h = req.params.get("h")
    cmd = ["screencapture", "-x"]
    if all(v is not None for v in [x, y, w, h]):
        cmd += ["-R", str(x) + "," + str(y) + "," + str(w) + "," + str(h)]
    cmd.append(str(out_path))
    rc, _, err = await _run(cmd)
    if rc != 0:
        return AdapterResponse.failure(req, "screencapture failed: " + err)
    img_bytes = out_path.read_bytes()
    img_hash = "sha256:" + hashlib.sha256(img_bytes).hexdigest()[:16]
    return AdapterResponse.success(req, {"path": str(out_path), "size_bytes": len(img_bytes), "hash": img_hash}, artifacts=[str(out_path)])

async def vision_ocr_region(req):
    run_id = req.run_id
    img_path = _artifact_path(run_id, "ocr_region.png")
    x = req.params.get("x", 0)
    y = req.params.get("y", 0)
    w = req.params.get("w", 400)
    h = req.params.get("h", 100)
    if MOCK_MODE:
        return AdapterResponse.success(req, {"text": "[MOCK OCR TEXT]", "confidence": 0.99, "region": {"x": x, "y": y, "w": w, "h": h}, "mock": True}, artifacts=[str(img_path)])
    rc, _, err = await _run(["screencapture", "-x", "-R", str(x) + "," + str(y) + "," + str(w) + "," + str(h), str(img_path)])
    if rc != 0:
        return AdapterResponse.failure(req, "screencapture failed: " + err)
    return AdapterResponse.success(req, {"text": None, "note": "swift ocr requires local run", "region": {"x": x, "y": y, "w": w, "h": h}}, artifacts=[str(img_path)])

async def fs_read_text(req):
    path = req.params.get("path", "")
    if not path:
        return AdapterResponse.failure(req, "params.path required")
    try:
        content = Path(path).read_text(errors="replace")
        return AdapterResponse.success(req, {"path": path, "content": content[:8192], "truncated": len(content) > 8192, "size_bytes": len(content.encode())})
    except FileNotFoundError:
        return AdapterResponse.failure(req, "FILE_NOT_FOUND: " + path)
    except PermissionError:
        return AdapterResponse.failure(req, "PERMISSION_DENIED: " + path)

async def fs_write_text(req):
    path = req.params.get("path", "")
    content = req.params.get("content", "")
    if not path:
        return AdapterResponse.failure(req, "params.path required")
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return AdapterResponse.success(req, {"path": path, "bytes_written": len(content.encode())})
    except PermissionError:
        return AdapterResponse.failure(req, "PERMISSION_DENIED: " + path)

async def fs_list(req):
    path = req.params.get("path", str(Path.home()))
    try:
        entries = []
        for item in sorted(Path(path).iterdir()):
            entries.append({"name": item.name, "type": "dir" if item.is_dir() else "file", "size_bytes": item.stat().st_size if item.is_file() else None})
        return AdapterResponse.success(req, {"path": path, "entries": entries[:100]})
    except PermissionError:
        return AdapterResponse.failure(req, "PERMISSION_DENIED: " + path)
    except FileNotFoundError:
        return AdapterResponse.failure(req, "PATH_NOT_FOUND: " + path)

def build_registry():
    reg = AdapterRegistry()
    reg.register_all({
        "env.health": env_health, "env.capabilities": env_capabilities, "env.version": env_version,
    })
    reg.register_all(build_vision_handlers())
    reg.register_all(build_fs_handlers())
    reg.register_all(build_input_handlers())
    reg.register_all(build_window_handlers())
    reg.register_all(build_network_handlers())
    reg.register_all(build_proc_extended_handlers())
    reg.register_all(build_file_watch_handlers())
    reg.register_all(build_audio_handlers())
    reg.register_all(build_clipboard_handlers())
    reg.register_all(build_notify_handlers())
    reg.register_all(build_display_handlers())
    reg.register_all(build_battery_handlers())
    reg.register_all(build_keychain_handlers())
    return reg
