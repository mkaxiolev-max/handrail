"""
Scans /Volumes/NSExternal (fallback ~/ALEXANDRIA) for files.
Returns list of {path, size, mtime, sha256} dicts.
Skips files whose hash matches the stored hash (unchanged).
"""
import os
import hashlib
from typing import List, Dict, Any

SCAN_ROOTS = [
    "/Volumes/NSExternal/ALEXANDRIA",
    os.path.expanduser("~/ALEXANDRIA"),
]

SKIP_EXTENSIONS = {".pyc", ".pyo", ".log", ".sock", ".pid"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB — skip larger files


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    except (IOError, OSError):
        return ""
    return h.hexdigest()


def scan(known_hashes: Dict[str, str] = None) -> List[Dict[str, Any]]:
    """
    Walk scan roots, return file records.
    known_hashes: {path: sha256} — files with matching hash are marked unchanged.
    """
    if known_hashes is None:
        known_hashes = {}

    results = []
    for root in SCAN_ROOTS:
        if not os.path.isdir(root):
            continue
        for dirpath, _, filenames in os.walk(root, followlinks=False):
            for fname in filenames:
                _, ext = os.path.splitext(fname)
                if ext in SKIP_EXTENSIONS:
                    continue
                fpath = os.path.join(dirpath, fname)
                try:
                    stat = os.stat(fpath)
                except OSError:
                    continue
                if stat.st_size > MAX_FILE_SIZE:
                    continue
                sha = _sha256(fpath)
                changed = known_hashes.get(fpath) != sha
                results.append({
                    "path": fpath,
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                    "sha256": sha,
                    "changed": changed,
                })
    return results
