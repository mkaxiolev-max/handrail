"""Source lane adapters. Each implements probe + fetch."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timezone
import logging
import os
import requests

from services.reality_ingest.schema import SourceLane, SourceTier, SourceCandidate

logger = logging.getLogger(__name__)
USER_AGENT = "AXIOLEV-NS-RIS/2.0 (research)"


@dataclass
class ProbeResult:
    available: bool
    url: Optional[str] = None
    file_pointer: Optional[str] = None
    status: Optional[int] = None
    content_type: Optional[str] = None
    byte_size: Optional[int] = None
    reason: Optional[str] = None


class SourceLaneAdapter(ABC):
    lane: SourceLane
    tier: SourceTier

    @abstractmethod
    def probe(self, target: str) -> ProbeResult: ...

    @abstractmethod
    def list_targets(self) -> List[str]: ...

    @abstractmethod
    def fetch(self, target: str, dest_dir: Path) -> dict: ...

    def candidate(self, target: str) -> SourceCandidate:
        p = self.probe(target)
        return SourceCandidate(
            lane=self.lane, tier=self.tier,
            url=p.url, file_pointer=p.file_pointer,
            available=p.available, reason=p.reason,
            probe_status=p.status, probe_content_type=p.content_type,
            probe_byte_size=p.byte_size,
        )


class PatentsViewS3Lane(SourceLaneAdapter):
    lane = SourceLane.PATENTSVIEW_S3
    tier = SourceTier.DERIVED_PUBLIC
    BASE = "https://s3.amazonaws.com/data.patentsview.org/download"

    TABLES = {
        "patent":             ("g_patent.tsv.zip",                    230),
        "patent_assignee":    ("g_assignee_disambiguated.tsv.zip",    360),
        "patent_inventor":    ("g_inventor_disambiguated.tsv.zip",    700),
        "patent_application": ("g_application.tsv.zip",                70),
        "patent_cpc":         ("g_cpc_current.tsv.zip",               500),
        "patent_us_citation": ("g_us_patent_citation.tsv.zip",       2230),
        "patent_figures":     ("g_figures.tsv.zip",                    50),
    }

    def list_targets(self) -> List[str]:
        return list(self.TABLES.keys())

    def url_for(self, target: str) -> str:
        if target not in self.TABLES:
            raise KeyError(f"unknown PatentsView target: {target}")
        fname, _mb = self.TABLES[target]
        return f"{self.BASE}/{fname}"

    def probe(self, target: str) -> ProbeResult:
        try:
            url = self.url_for(target)
        except KeyError as e:
            return ProbeResult(False, reason=str(e))
        try:
            r = requests.head(url, headers={"User-Agent": USER_AGENT},
                              timeout=10, allow_redirects=True)
            ct = r.headers.get("Content-Type", "")
            cl = r.headers.get("Content-Length")
            ok = r.status_code == 200 and ("zip" in ct.lower() or "octet" in ct.lower() or url.endswith(".zip"))
            return ProbeResult(
                available=ok, url=url, status=r.status_code,
                content_type=ct, byte_size=int(cl) if cl else None,
                reason=None if ok else f"unexpected status/ct: {r.status_code} {ct}"
            )
        except Exception as e:
            return ProbeResult(False, url=url, reason=f"probe error: {e}")

    def fetch(self, target: str, dest_dir: Path) -> dict:
        url = self.url_for(target)
        fname = url.rsplit("/", 1)[-1]
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / fname
        if dest.exists() and dest.stat().st_size > 1_000_000:
            return {"path": str(dest), "size": dest.stat().st_size,
                    "url": url, "cached": True}
        tmp = dest.with_suffix(".part")
        size = 0
        with requests.get(url, stream=True, timeout=600,
                          headers={"User-Agent": USER_AGENT}) as r:
            r.raise_for_status()
            with tmp.open("wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 20):
                    if chunk:
                        f.write(chunk)
                        size += len(chunk)
                f.flush()
                os.fsync(f.fileno())
        tmp.rename(dest)
        return {"path": str(dest), "size": size, "url": url, "cached": False}


class USPTOODPApiLane(SourceLaneAdapter):
    lane = SourceLane.USPTO_ODP_API
    tier = SourceTier.OFFICIAL_AUTHENTICATED
    API_BASE = "https://data.uspto.gov/api/v1"

    PRODUCTS = {
        "PTGRXML": "Patent Grant Full-Text XML (weekly)",
        "PASDL":   "Patent Assignment Daily",
        "PTFWPRD": "Patent File Wrapper Daily",
        "CPCG":    "CPC Classification (Grants, monthly)",
    }

    def __init__(self):
        self.token = os.environ.get("USPTO_ODP_TOKEN")

    @property
    def is_authenticated(self) -> bool:
        return bool(self.token)

    def list_targets(self) -> List[str]:
        return list(self.PRODUCTS.keys())

    def probe(self, target: str) -> ProbeResult:
        if not self.token:
            return ProbeResult(
                available=False,
                url=f"{self.API_BASE}/datasets/products/{target}",
                reason="dormant: USPTO_ODP_TOKEN env var not set. "
                       "Register at https://data.uspto.gov via ID.me to obtain key."
            )
        try:
            url = f"{self.API_BASE}/datasets/products/{target}"
            r = requests.get(url, headers={"X-API-KEY": self.token,
                                            "User-Agent": USER_AGENT}, timeout=15)
            return ProbeResult(
                available=r.status_code == 200, url=url,
                status=r.status_code,
                content_type=r.headers.get("Content-Type"),
                reason=None if r.status_code == 200 else f"status {r.status_code}"
            )
        except Exception as e:
            return ProbeResult(False, reason=f"probe error: {e}")

    def fetch(self, target: str, dest_dir: Path) -> dict:
        if not self.token:
            raise RuntimeError("USPTO_ODP_TOKEN not set; cannot fetch via ODP")
        raise NotImplementedError(
            "ODP fetch not yet wired. Requires: "
            "(1) /datasets/products/{PID}/files metadata call, "
            "(2) /bulk-data/download with signed-URL follow, "
            "(3) sequential request scheduler."
        )


class LocalInboxLane(SourceLaneAdapter):
    lane = SourceLane.LOCAL_INBOX
    tier = SourceTier.MANUAL
    INBOX = Path("/Volumes/NSExternal/ris/uspto/inbox")

    def list_targets(self) -> List[str]:
        if not self.INBOX.exists():
            return []
        return [p.name for p in self.INBOX.glob("*.zip")]

    def probe(self, target: str) -> ProbeResult:
        path = self.INBOX / target
        if not path.exists():
            return ProbeResult(False, file_pointer=str(path), reason="not in inbox")
        size = path.stat().st_size
        return ProbeResult(available=True, file_pointer=str(path),
                           byte_size=size, content_type="application/zip")

    def fetch(self, target: str, dest_dir: Path) -> dict:
        path = self.INBOX / target
        if not path.exists():
            raise FileNotFoundError(f"{target} not in inbox")
        return {"path": str(path), "size": path.stat().st_size,
                "url": f"file://{path}", "cached": True}
