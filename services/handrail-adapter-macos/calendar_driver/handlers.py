"""
calendar.* namespace
====================
macOS Calendar read access via osascript.

Ops:
  calendar.today      — events for today
  calendar.upcoming   — next N events across all calendars
  calendar.list       — list all calendar names

Dignity Guard:
  Read-only. No event creation or modification.
  Calendar access requires user permission (graceful skip if denied).
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


async def calendar_list(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "calendars": [], "mode": "mock"})
    script = 'tell application "Calendar" to get name of every calendar'
    rc, out, err = await _run(["osascript", "-e", script])
    if rc != 0:
        return AdapterResponse.success(req, {"ok": True, "calendars": [],
                                              "skipped": True, "reason": "calendar_access_denied"})
    calendars = [c.strip() for c in out.split(",") if c.strip()]
    return AdapterResponse.success(req, {"ok": True, "calendars": calendars, "count": len(calendars)})


async def calendar_today(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "events": [], "mode": "mock"})
    script = '''
tell application "Calendar"
    set todayEvents to {}
    set today to current date
    set startOfDay to today - (time of today)
    set endOfDay to startOfDay + (23 * hours + 59 * minutes + 59)
    repeat with cal in calendars
        try
            set evts to (every event of cal whose start date >= startOfDay and start date <= endOfDay)
            repeat with evt in evts
                set end of todayEvents to (summary of evt & " @ " & (start date of evt as string))
            end repeat
        end try
    end repeat
    return todayEvents
end tell
'''
    rc, out, err = await _run(["osascript", "-e", script])
    if rc != 0:
        return AdapterResponse.success(req, {"ok": True, "events": [],
                                              "skipped": True, "reason": str(err)[:80]})
    events = [e.strip() for e in out.split(",") if e.strip()] if out else []
    return AdapterResponse.success(req, {"ok": True, "events": events, "count": len(events)})


async def calendar_upcoming(req: AdapterRequest) -> AdapterResponse:
    n = int((req.params or {}).get("n", 5))
    n = min(n, 20)
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "events": [], "mode": "mock"})
    script = f'''
tell application "Calendar"
    set upcomingEvents to {{}}
    set now to current date
    set futureDate to now + (7 * days)
    repeat with cal in calendars
        try
            set evts to (every event of cal whose start date >= now and start date <= futureDate)
            repeat with evt in evts
                set end of upcomingEvents to (summary of evt & "|" & (start date of evt as string))
            end repeat
        end try
    end repeat
    return upcomingEvents
end tell
'''
    rc, out, err = await _run(["osascript", "-e", script])
    if rc != 0:
        return AdapterResponse.success(req, {"ok": True, "events": [],
                                              "skipped": True, "reason": str(err)[:80]})
    events = [e.strip() for e in out.split(",") if e.strip()][:n]
    return AdapterResponse.success(req, {"ok": True, "events": events, "count": len(events)})


def build_calendar_handlers() -> dict:
    return {
        "calendar.list":     calendar_list,
        "calendar.today":    calendar_today,
        "calendar.upcoming": calendar_upcoming,
    }
