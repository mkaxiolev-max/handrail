"""
NORTHSTAR Storage Layer
Directory bootstrap, write barriers, content-addressable store.
Enforces: Alexandria (high-entropy) cannot silently overwrite Canon.
"""

import os
import json
import hashlib
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any


# ─── Path constants ────────────────────────────────────────────────────────────

EXTERNAL_SSD = Path(os.environ.get("NORTHSTAR_SSD_MOUNT", "/Volumes/NSExternal"))
# Local fallback when SSD not mounted (auto-detected at runtime)
def _get_alexandria_root() -> Path:
    """Returns configured Alexandria root.

    Priority:
      1) NORTHSTAR_ALEXANDRIA_ROOT (explicit)
      2) SSD mount (NORTHSTAR_SSD_MOUNT)/ALEXANDRIA if mounted
      3) ~/ALEXANDRIA fallback

    Note: this chooses the *root*, not a subfolder.
    """
    explicit = os.environ.get("NORTHSTAR_ALEXANDRIA_ROOT", "").strip()
    if explicit:
        p = Path(explicit).expanduser()
        p.mkdir(parents=True, exist_ok=True)
        return p

    if EXTERNAL_SSD.exists():
        p = EXTERNAL_SSD / "ALEXANDRIA"
        p.mkdir(parents=True, exist_ok=True)
        return p

    local = Path.home() / "ALEXANDRIA"
    local.mkdir(parents=True, exist_ok=True)
    return local

INTERNAL_HOME = Path.home()

ALEXANDRIA_ROOT    = _get_alexandria_root()
ETHER_DIR          = ALEXANDRIA_ROOT / "ether"
INDEX_DIR          = ALEXANDRIA_ROOT / "index"
PROTO_CANON_DIR    = ALEXANDRIA_ROOT / "proto_canon"
RECEIPT_LEDGER_DIR = ALEXANDRIA_ROOT / "receipt_ledger"

MANIFOLD_ROOT      = Path(os.environ.get("NORTHSTAR_MANIFOLD_ROOT", str(INTERNAL_HOME / "NSS" / "MANIFOLD"))).expanduser()
CANON_DIR          = MANIFOLD_ROOT / "canon"
MISSION_GRAPH_DIR  = MANIFOLD_ROOT / "mission_graph"
CONFIG_DIR         = Path(os.environ.get("NORTHSTAR_CONFIG_ROOT", str(INTERNAL_HOME / "NSS" / "configs"))).expanduser()
LOG_DIR            = Path(os.environ.get("NORTHSTAR_LOG_ROOT", str(INTERNAL_HOME / "NSS" / "logs"))).expanduser()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


class StorageLayout:
    """
    Bootstraps and enforces the full directory structure per the MVP spec.
    Call bootstrap() once at startup.
    """

    REQUIRED_DIRS = [
        ETHER_DIR,
        ETHER_DIR / "voice",
        ETHER_DIR / "files",
        ETHER_DIR / "events",
        INDEX_DIR,
        PROTO_CANON_DIR,
        RECEIPT_LEDGER_DIR,
        MANIFOLD_ROOT,
        CANON_DIR,
        MISSION_GRAPH_DIR,
        CONFIG_DIR,
        LOG_DIR,
    ]

    def bootstrap(self) -> Dict[str, Any]:
        """
        Create all required directories. Return health status.
        """
        status = {
            "external_ssd_mounted": EXTERNAL_SSD.exists(),
            "directories_created": [],
            "directories_existed": [],
            "errors": [],
        }

        if not EXTERNAL_SSD.exists():
            status["errors"].append(f"External SSD not mounted at {EXTERNAL_SSD}")
            # Still create internal dirs
            dirs = [d for d in self.REQUIRED_DIRS if not str(d).startswith(str(EXTERNAL_SSD))]
        else:
            dirs = self.REQUIRED_DIRS

        for d in dirs:
            try:
                if d.exists():
                    status["directories_existed"].append(str(d))
                else:
                    d.mkdir(parents=True, exist_ok=True)
                    status["directories_created"].append(str(d))
            except Exception as e:
                status["errors"].append(f"{d}: {e}")

        return status

    def health(self) -> Dict[str, Any]:
        return {
            "external_ssd": EXTERNAL_SSD.exists(),
            "alexandria": ALEXANDRIA_ROOT.exists(),
            "ether": ETHER_DIR.exists(),
            "proto_canon": PROTO_CANON_DIR.exists(),
            "receipt_ledger": RECEIPT_LEDGER_DIR.exists(),
            "manifold": MANIFOLD_ROOT.exists(),
            "canon": CANON_DIR.exists(),
            "mission_graph": MISSION_GRAPH_DIR.exists(),
        }


class ContentStore:
    """
    Content-addressable store (CAS) living in Alexandria/index/.
    Write once, addressed by SHA-256 of content.
    """

    def __init__(self, store_dir: Path = INDEX_DIR):
        self.store_dir = store_dir
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def put_bytes(self, data: bytes, metadata: Optional[Dict] = None) -> str:
        """Store bytes, return content hash."""
        content_hash = _sha256_bytes(data)
        short = content_hash[7:15]  # first 8 hex chars after 'sha256:'
        shard = self.store_dir / short[:2]
        shard.mkdir(exist_ok=True)

        blob_path = shard / short
        if not blob_path.exists():
            blob_path.write_bytes(data)

        # Write metadata sidecar
        if metadata:
            meta_path = shard / (short + ".meta.json")
            with open(meta_path, "w") as f:
                json.dump({
                    "content_hash": content_hash,
                    "size": len(data),
                    "ts_utc": datetime.now(timezone.utc).isoformat(),
                    **metadata
                }, f, indent=2)

        return content_hash

    def put_text(self, text: str, metadata: Optional[Dict] = None) -> str:
        return self.put_bytes(text.encode(), metadata)

    def put_file(self, path: Path, metadata: Optional[Dict] = None) -> str:
        """Store a file by content hash. Returns hash."""
        data = path.read_bytes()
        meta = {"original_path": str(path), "filename": path.name}
        if metadata:
            meta.update(metadata)
        return self.put_bytes(data, meta)

    def get(self, content_hash: str) -> Optional[bytes]:
        short = content_hash[7:15]
        shard = self.store_dir / short[:2]
        blob_path = shard / short
        if blob_path.exists():
            return blob_path.read_bytes()
        return None

    def exists(self, content_hash: str) -> bool:
        short = content_hash[7:15]
        return (self.store_dir / short[:2] / short).exists()


class CanonStore:
    """
    Guarded canon store. Writes only after explicit gate pass.
    Lives at ~/NSS/MANIFOLD/canon/
    """

    def __init__(self, canon_dir: Path = CANON_DIR):
        self.canon_dir = canon_dir
        self.canon_dir.mkdir(parents=True, exist_ok=True)

    def write(self, claim_id: str, entry: Dict[str, Any], receipt_hash: str) -> Path:
        """
        Write a canon entry. Requires receipt_hash to prove gate was passed.
        """
        if not receipt_hash or not receipt_hash.startswith("sha256:"):
            raise ValueError("Canon write requires valid receipt_hash")

        entry["_receipt_hash"] = receipt_hash
        entry["_ts_utc"] = datetime.now(timezone.utc).isoformat()
        entry["_claim_id"] = claim_id

        canon_file = self.canon_dir / f"{claim_id}.json"
        with open(canon_file, "w") as f:
            json.dump(entry, f, indent=2)

        return canon_file

    def read(self, claim_id: str) -> Optional[Dict]:
        p = self.canon_dir / f"{claim_id}.json"
        if p.exists():
            return json.loads(p.read_text())
        return None

    def list_claims(self):
        return [p.stem for p in self.canon_dir.glob("*.json")]


class EtherStore:
    """
    Writable ether store for raw ingested signals.
    Lives at /ALEXANDRIA/ether/
    """

    def __init__(self, ether_dir: Path = ETHER_DIR):
        self.ether_dir = ether_dir

    def store_voice(self, audio_bytes: bytes, call_sid: str, ts: Optional[str] = None) -> Path:
        now = datetime.now(timezone.utc)
        day_dir = self.ether_dir / "voice" / now.strftime("%Y/%m/%d")
        day_dir.mkdir(parents=True, exist_ok=True)
        fname = f"{call_sid}_{now.strftime('%H%M%S')}.wav"
        path = day_dir / fname
        path.write_bytes(audio_bytes)
        return path

    def store_event(self, event: Dict[str, Any]) -> Path:
        now = datetime.now(timezone.utc)
        day_dir = self.ether_dir / "events" / now.strftime("%Y/%m/%d")
        day_dir.mkdir(parents=True, exist_ok=True)
        fname = f"{now.strftime('%H%M%S')}_{event.get('type', 'event')}.json"
        path = day_dir / fname
        with open(path, "w") as f:
            json.dump(event, f, indent=2)
        return path

    def store_file(self, data: bytes, filename: str) -> Path:
        day_dir = self.ether_dir / "files" / datetime.now(timezone.utc).strftime("%Y/%m/%d")
        day_dir.mkdir(parents=True, exist_ok=True)
        path = day_dir / filename
        path.write_bytes(data)
        return path


# Singleton instances (initialized after bootstrap)
_layout = StorageLayout()
_cas = None
_canon = None
_ether = None


def bootstrap() -> Dict[str, Any]:
    global _cas, _canon, _ether
    status = _layout.bootstrap()
    _cas = ContentStore()
    _canon = CanonStore()
    _ether = EtherStore()
    return status


def get_cas() -> ContentStore:
    global _cas
    if _cas is None:
        _cas = ContentStore()
    return _cas


def get_canon() -> CanonStore:
    global _canon
    if _canon is None:
        _canon = CanonStore()
    return _canon


def get_ether() -> EtherStore:
    global _ether
    if _ether is None:
        _ether = EtherStore()
    return _ether


def health() -> Dict[str, Any]:
    return _layout.health()
