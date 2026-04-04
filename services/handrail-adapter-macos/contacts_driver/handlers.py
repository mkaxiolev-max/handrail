"""
contacts.* namespace
====================
macOS Contacts read access via osascript.

Ops:
  contacts.search   — search by name, returns [{name, email, phone}]
  contacts.count    — total contact count
  contacts.vcard    — export single contact as vCard string

Dignity Guard:
  Read-only — no contact modification.
  Returns max 10 results per search.
  Phone/email fields only — no address, birthday, notes.
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


async def contacts_search(req: AdapterRequest) -> AdapterResponse:
    query = (req.params or {}).get("query", "").strip()[:100]
    if not query:
        return AdapterResponse.failure(req, "query required")
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "contacts": [], "count": 0, "mode": "mock"})
    script = f'''
tell application "Contacts"
    set results to {{}}
    set matches to (every person whose name contains "{query}" or email contains "{query}")
    repeat with p in matches
        try
            set pname to name of p
            set pemail to ""
            if (count of emails of p) > 0 then set pemail to value of item 1 of emails of p
            set pphone to ""
            if (count of phones of p) > 0 then set pphone to value of item 1 of phones of p
            set end of results to (pname & "|" & pemail & "|" & pphone)
        end try
    end repeat
    return results
end tell
'''
    rc, out, err = await _run(["osascript", "-e", script])
    if rc != 0:
        return AdapterResponse.success(req, {"ok": True, "contacts": [],
                                              "skipped": True, "reason": str(err)[:80]})
    contacts = []
    for line in out.split(",")[:10]:
        parts = line.strip().split("|")
        if parts:
            contacts.append({
                "name": parts[0].strip() if len(parts) > 0 else "",
                "email": parts[1].strip() if len(parts) > 1 else "",
                "phone": parts[2].strip() if len(parts) > 2 else "",
            })
    return AdapterResponse.success(req, {"ok": True, "contacts": contacts, "count": len(contacts)})


async def contacts_count(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "count": 0, "mode": "mock"})
    script = 'tell application "Contacts" to count every person'
    rc, out, err = await _run(["osascript", "-e", script])
    if rc != 0:
        return AdapterResponse.success(req, {"ok": True, "count": 0,
                                              "skipped": True, "reason": str(err)[:60]})
    try:
        count = int(out.strip())
    except ValueError:
        count = 0
    return AdapterResponse.success(req, {"ok": True, "count": count})


async def contacts_vcard(req: AdapterRequest) -> AdapterResponse:
    name = (req.params or {}).get("name", "").strip()[:100]
    if not name:
        return AdapterResponse.failure(req, "name required")
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "vcard": "", "mode": "mock"})
    script = f'''
tell application "Contacts"
    set matches to (every person whose name = "{name}")
    if (count of matches) = 0 then return ""
    set p to item 1 of matches
    set vcard to "BEGIN:VCARD" & return & "VERSION:3.0" & return
    set vcard to vcard & "FN:" & name of p & return
    if (count of emails of p) > 0 then
        set vcard to vcard & "EMAIL:" & (value of item 1 of emails of p) & return
    end if
    set vcard to vcard & "END:VCARD"
    return vcard
end tell
'''
    rc, out, err = await _run(["osascript", "-e", script])
    if rc != 0:
        return AdapterResponse.success(req, {"ok": True, "vcard": None,
                                              "skipped": True, "reason": str(err)[:60]})
    return AdapterResponse.success(req, {"ok": True, "vcard": out, "found": bool(out)})


def build_contacts_handlers() -> dict:
    return {
        "contacts.search": contacts_search,
        "contacts.count":  contacts_count,
        "contacts.vcard":  contacts_vcard,
    }
