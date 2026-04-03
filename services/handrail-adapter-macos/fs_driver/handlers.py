"""
fs.* namespace
==============
Local filesystem read/write/list ops.

Ops:
  fs.read_text  — {path, content, truncated, size_bytes}
  fs.write_text — {path, bytes_written}
  fs.list       — {path, entries: [{name, type, size_bytes}], count}

Dignity Guard:
  fs.read_text:  file must exist, size < 100 KB, must not be ALEXANDRIA/ledger
  fs.write_text: path must be under /tmp, ~/.axiolev, or
                 /Volumes/NSExternal/ALEXANDRIA/programs
"""
from __future__ import annotations
from pathlib import Path
from adapter_core.contract import AdapterRequest, AdapterResponse

_MAX_READ_BYTES = 100 * 1024  # 100 KB
_LEDGER_GUARD   = "ALEXANDRIA/ledger"

_WRITE_ALLOWED_ROOTS = (
    Path("/tmp"),
    Path.home() / ".axiolev",
    Path("/Volumes/NSExternal/ALEXANDRIA/programs"),
)


def _write_allowed(path: Path) -> bool:
    resolved = path.resolve() if path.exists() else path.absolute()
    for root in _WRITE_ALLOWED_ROOTS:
        try:
            resolved.relative_to(root.resolve())
            return True
        except ValueError:
            continue
    return False


async def fs_read_text(req: AdapterRequest) -> AdapterResponse:
    path_str = req.params.get("path", "")
    if not path_str:
        return AdapterResponse.failure(req, "params.path required")

    # Dignity Guard — block ledger reads
    if _LEDGER_GUARD in path_str:
        return AdapterResponse.denied(req, "fs.read_text blocked: ledger path is protected")

    p = Path(path_str)
    if not p.exists():
        return AdapterResponse.failure(req, f"FILE_NOT_FOUND: {path_str}")

    size = p.stat().st_size
    if size > _MAX_READ_BYTES:
        return AdapterResponse.failure(req, f"FILE_TOO_LARGE: {size} bytes > 100 KB limit")

    try:
        content = p.read_text(errors="replace")
    except PermissionError:
        return AdapterResponse.failure(req, f"PERMISSION_DENIED: {path_str}")

    truncated = len(content.encode()) > 8192
    return AdapterResponse.success(req, {
        "path": path_str,
        "content": content[:8192],
        "truncated": truncated,
        "size_bytes": size,
    })


async def fs_write_text(req: AdapterRequest) -> AdapterResponse:
    path_str = req.params.get("path", "")
    content  = req.params.get("content", "")
    if not path_str:
        return AdapterResponse.failure(req, "params.path required")

    p = Path(path_str)

    # Dignity Guard — restrict write paths
    if not _write_allowed(p):
        return AdapterResponse.denied(req, f"fs.write_text: path not in allowed roots: {path_str}")

    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    except PermissionError:
        return AdapterResponse.failure(req, f"PERMISSION_DENIED: {path_str}")

    return AdapterResponse.success(req, {
        "path": path_str,
        "bytes_written": len(content.encode()),
    })


async def fs_list(req: AdapterRequest) -> AdapterResponse:
    path_str = req.params.get("path", str(Path.home()))
    p = Path(path_str)

    if not p.exists():
        return AdapterResponse.failure(req, f"PATH_NOT_FOUND: {path_str}")

    try:
        entries = []
        for item in sorted(p.iterdir()):
            entries.append({
                "name": item.name,
                "type": "dir" if item.is_dir() else "file",
                "size_bytes": item.stat().st_size if item.is_file() else None,
            })
    except PermissionError:
        return AdapterResponse.failure(req, f"PERMISSION_DENIED: {path_str}")

    return AdapterResponse.success(req, {
        "path": path_str,
        "entries": entries[:100],
        "count": len(entries),
    })


def build_fs_handlers() -> dict:
    return {
        "fs.read_text":  fs_read_text,
        "fs.write_text": fs_write_text,
        "fs.list":       fs_list,
    }
