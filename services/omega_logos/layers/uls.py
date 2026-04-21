"""ULS layer — User's Local System bridge.
Read/write locally with receipt + diff. Unsafe actions blocked by policy.
AXIOLEV Holdings LLC © 2026. (Maps to I₆.C3 + I₆.C5.)"""
import hashlib, os, tempfile
from dataclasses import dataclass
from typing import Optional

def _resolve(p: str) -> str:
    return os.path.realpath(os.path.abspath(p))

SAFE_ROOTS = tuple(_resolve(r) for r in (
    os.path.expanduser("~/axiolev_runtime"),
    os.path.expanduser("~/.ns_max"),
    os.path.expanduser("~/.ns_omega"),
    tempfile.gettempdir(),
))

@dataclass
class FileOp:
    kind: str       # read | write
    path: str
    before_sha: Optional[str] = None
    after_sha:  Optional[str] = None

def _sha(p: str) -> Optional[str]:
    try:
        with open(p, "rb") as f: return hashlib.sha256(f.read()).hexdigest()
    except FileNotFoundError:
        return None

def _safe(path: str) -> bool:
    apath = _resolve(path)
    return any(apath.startswith(r) for r in SAFE_ROOTS)

def read_local(path: str) -> tuple[bool, str|None, FileOp]:
    if not _safe(path): return False, None, FileOp("read", path, None, None)
    op = FileOp("read", path, _sha(path), None)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return True, f.read(), op

def write_local(path: str, content: str) -> tuple[bool, FileOp]:
    if not _safe(path): return False, FileOp("write", path, None, None)
    before = _sha(path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f: f.write(content)
    op = FileOp("write", path, before, _sha(path))
    return True, op
