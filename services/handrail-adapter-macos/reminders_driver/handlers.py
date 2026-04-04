"""
reminders.* namespace
=====================
macOS Reminders read/write via osascript.

Ops:
  reminders.list      — list incomplete reminders
  reminders.add       — add a new reminder (dignity: max 200 chars)
  reminders.complete  — mark reminder complete by name match

Dignity Guard:
  Add: text max 200 chars.
  Complete: only matches by exact name — no wildcard deletes.
  No bulk operations.
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


async def reminders_list(req: AdapterRequest) -> AdapterResponse:
    list_name = (req.params or {}).get("list", "Reminders")[:50]
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "reminders": [], "count": 0, "mode": "mock"})
    script = f'''
tell application "Reminders"
    set remList to {{}}
    try
        set rl to list "{list_name}"
        set rems to (every reminder of rl whose completed is false)
        repeat with r in rems
            set end of remList to name of r
        end repeat
    end try
    return remList
end tell
'''
    rc, out, err = await _run(["osascript", "-e", script])
    if rc != 0:
        return AdapterResponse.success(req, {"ok": True, "reminders": [],
                                              "skipped": True, "reason": str(err)[:80]})
    items = [r.strip() for r in out.split(",") if r.strip()] if out else []
    return AdapterResponse.success(req, {"ok": True, "reminders": items[:20], "count": len(items)})


async def reminders_add(req: AdapterRequest) -> AdapterResponse:
    text = (req.params or {}).get("text", "").strip()[:200]
    list_name = (req.params or {}).get("list", "Reminders")[:50]
    if not text:
        return AdapterResponse.failure(req, "text required")
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "added": True, "text": text, "mode": "mock"})
    safe_text = text.replace('"', '\\"')
    script = f'''
tell application "Reminders"
    tell list "{list_name}"
        make new reminder with properties {{name:"{safe_text}"}}
    end tell
end tell
'''
    rc, out, err = await _run(["osascript", "-e", script])
    if rc != 0:
        return AdapterResponse.failure(req, f"add reminder failed: {err[:80]}")
    return AdapterResponse.success(req, {"ok": True, "added": True, "text": text})


async def reminders_complete(req: AdapterRequest) -> AdapterResponse:
    name = (req.params or {}).get("name", "").strip()[:200]
    list_name = (req.params or {}).get("list", "Reminders")[:50]
    if not name:
        return AdapterResponse.failure(req, "name required")
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "completed": True, "mode": "mock"})
    safe_name = name.replace('"', '\\"')
    script = f'''
tell application "Reminders"
    tell list "{list_name}"
        set matches to (every reminder whose name = "{safe_name}")
        if (count of matches) = 0 then return "not_found"
        set completed of item 1 of matches to true
        return "ok"
    end tell
end tell
'''
    rc, out, err = await _run(["osascript", "-e", script])
    if rc != 0 or out == "not_found":
        return AdapterResponse.success(req, {"ok": True, "completed": False,
                                              "reason": "not_found" if out == "not_found" else str(err)[:60]})
    return AdapterResponse.success(req, {"ok": True, "completed": True, "name": name})


def build_reminders_handlers() -> dict:
    return {
        "reminders.list":     reminders_list,
        "reminders.add":      reminders_add,
        "reminders.complete": reminders_complete,
    }
