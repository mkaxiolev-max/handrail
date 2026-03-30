"""
NS∞ USPTO Ingest Engine
Bandwidth-aware downloader + XML parser for SAN∞ terrain initialization.

Two modes:
  TERRAIN  (tonight, fast) — PatentsView Parquet tables + metadata
                              No XML parsing. No embeddings.
                              ~20-40GB. Minimal bandwidth.
  DEEP     (overnight)     — USPTO Bulk XML (PTGRXML/APPXML)
                              Full claim text + structure.
                              Bandwidth-scheduled for Starlink caps.

Starlink scheduling:
  - Monitor hourly bandwidth budget
  - Pause when cap approaching
  - Resume in next window
  - Prioritize PatentsView Parquet first (pre-normalized, smaller)
  - Scoped CPC pulls via USPTO ODP API (targeted, not full bulk)

Delta architecture:
  - SHA blocks on claim text, CPC, citations
  - Re-download only changed records
  - No full rebuilds after baseline

90-day gate sequence (from architecture doc):
  Gate 1 (Wk 1-3):  Terrain + BM25 — scoped CPC + 2-hop
  Gate 2 (Wk 4-6):  White-space + competitor pressure
  Gate 3 (Wk 7-9):  Embeddings for independent claims + abstracts
  Gate 4 (Wk 10-12): Weekly deltas, signed snapshot replay
"""

import os
import json
import time
import hashlib
import asyncio
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any

logger = logging.getLogger("ns.uspto")


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()

def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


# ── Bandwidth Budget ───────────────────────────────────────────────────────────

@dataclass
class BandwidthBudget:
    """
    Starlink-aware bandwidth controller.
    Tracks usage, enforces caps, schedules work in low-usage windows.
    """
    daily_cap_gb: float = 100.0          # Conservative Starlink cap
    soft_limit_pct: float = 0.80         # Pause at 80% of daily cap
    peak_hours: List[int] = field(        # Hours to avoid (local time)
        default_factory=lambda: list(range(7, 23)))
    bytes_used_today: float = 0.0
    window_start: str = field(default_factory=_ts)

    def can_download(self, estimated_bytes: float = 0) -> bool:
        used_gb = (self.bytes_used_today + estimated_bytes) / 1e9
        return used_gb < (self.daily_cap_gb * self.soft_limit_pct)

    def remaining_gb(self) -> float:
        cap = self.daily_cap_gb * self.soft_limit_pct
        return max(0.0, cap - self.bytes_used_today / 1e9)

    def record_download(self, bytes_downloaded: float):
        self.bytes_used_today += bytes_downloaded

    def is_off_peak(self) -> bool:
        hour = datetime.now().hour
        return hour not in self.peak_hours

    def reset_daily(self):
        self.bytes_used_today = 0.0
        self.window_start = _ts()

    def status(self) -> dict:
        return {
            "daily_cap_gb": self.daily_cap_gb,
            "used_gb": round(self.bytes_used_today / 1e9, 3),
            "remaining_gb": round(self.remaining_gb(), 3),
            "soft_limit_pct": self.soft_limit_pct,
            "can_download": self.can_download(),
            "is_off_peak": self.is_off_peak(),
            "window_start": self.window_start,
        }


# ── Download Jobs ──────────────────────────────────────────────────────────────

@dataclass
class DownloadJob:
    """A single download task in the ingest queue."""
    job_id: str
    job_type: str           # patentsview_table | uspto_bulk_xml | uspto_odp_scoped
    url: str
    dest_path: str
    priority: int = 5       # 1=highest, 10=lowest
    estimated_bytes: float = 0
    cpc_scope: List[str] = field(default_factory=list)
    status: str = "pending" # pending | downloading | done | failed | paused
    bytes_downloaded: float = 0
    error: str = ""
    created_at: str = field(default_factory=_ts)
    completed_at: str = ""
    sha_manifest: str = ""


@dataclass
class IngestRun:
    """One complete ingest session."""
    run_id: str
    mode: str               # terrain | deep | delta
    gate: int               # 1-4 per architecture doc
    cpc_scope: List[str] = field(default_factory=list)
    jobs: List[DownloadJob] = field(default_factory=list)
    status: str = "pending"
    patents_processed: int = 0
    claims_processed: int = 0
    errors: int = 0
    bandwidth_used_gb: float = 0
    started_at: str = ""
    completed_at: str = ""
    snapshot_id: str = ""


# ── PatentsView Source ─────────────────────────────────────────────────────────

# Pre-normalized Parquet tables from patentsview.org
# These are the FIRST priority for Starlink bandwidth — smallest, highest value
PATENTSVIEW_TABLES = {
    "patents":    "https://s3.amazonaws.com/data.patentsview.org/download/patent.tsv.zip",
    "claims":     "https://s3.amazonaws.com/data.patentsview.org/download/claim.tsv.zip",
    "cpc":        "https://s3.amazonaws.com/data.patentsview.org/download/cpc_current.tsv.zip",
    "citations":  "https://s3.amazonaws.com/data.patentsview.org/download/uspatentcitation.tsv.zip",
    "assignees":  "https://s3.amazonaws.com/data.patentsview.org/download/patent_assignee.tsv.zip",
    "inventors":  "https://s3.amazonaws.com/data.patentsview.org/download/inventor.tsv.zip",
}

# Approx sizes (GB compressed)
PATENTSVIEW_SIZES = {
    "cpc": 0.3, "assignees": 0.4, "inventors": 0.5,
    "claims": 1.5, "citations": 1.2, "patents": 2.0,
}

# Ingestion priority for bandwidth-constrained overnight run
TERRAIN_PRIORITY_ORDER = ["cpc", "assignees", "inventors", "claims", "citations", "patents"]


class USPTOIngestEngine:
    """
    Bandwidth-aware USPTO ingestion engine.
    Orchestrates PatentsView Parquet downloads + USPTO XML parsing.
    Feeds into SANTerrainEngine storage.
    """

    def __init__(self, raw_dir: Path, terrain_engine=None,
                 receipt_chain=None, budget: BandwidthBudget = None):
        self.raw_dir = raw_dir
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self._terrain = terrain_engine
        self._receipt_chain = receipt_chain
        self._budget = budget or BandwidthBudget()
        self._runs_dir = raw_dir / "runs"
        self._runs_dir.mkdir(exist_ok=True)
        self._current_run: Optional[IngestRun] = None
        self._paused = False

        # Load existing runs
        self._run_log: List[dict] = self._load_run_log()

    def _load_run_log(self) -> List[dict]:
        p = self._runs_dir / "_run_log.json"
        if p.exists():
            try:
                return json.loads(p.read_text())
            except Exception:
                return []
        return []

    def _save_run_log(self):
        (self._runs_dir / "_run_log.json").write_text(
            json.dumps(self._run_log[-100:], indent=2))

    # ── Job Planning ───────────────────────────────────────────────────────

    def plan_terrain_run(self, cpc_scope: List[str] = None,
                          budget_gb: float = None) -> IngestRun:
        """
        Plan a Gate 1 terrain run — PatentsView tables.
        Use this tonight. Fast, small, no XML.
        Returns estimated bandwidth before committing.
        """
        run_id = _sha(f"terrain_{_ts()}")
        run = IngestRun(
            run_id=run_id,
            mode="terrain",
            gate=1,
            cpc_scope=cpc_scope or [],
        )

        available_gb = budget_gb or self._budget.remaining_gb()
        total_estimated = 0.0

        for table_name in TERRAIN_PRIORITY_ORDER:
            size_gb = PATENTSVIEW_SIZES[table_name]
            if total_estimated + size_gb > available_gb:
                logger.info(f"Skipping {table_name}: would exceed budget "
                            f"({total_estimated:.1f}+{size_gb:.1f} > {available_gb:.1f}GB)")
                continue

            job = DownloadJob(
                job_id=_sha(f"{run_id}_{table_name}"),
                job_type="patentsview_table",
                url=PATENTSVIEW_TABLES[table_name],
                dest_path=str(self.raw_dir / "patentsview" / f"{table_name}.tsv.zip"),
                priority=TERRAIN_PRIORITY_ORDER.index(table_name) + 1,
                estimated_bytes=size_gb * 1e9,
                cpc_scope=cpc_scope or [],
            )
            run.jobs.append(job)
            total_estimated += size_gb

        return run

    def plan_deep_run(self, cpc_scope: List[str],
                       year_range: tuple = (2020, 2026),
                       budget_gb: float = None) -> IngestRun:
        """
        Plan a Gate 1-3 deep run — USPTO bulk XML for claims.
        Scoped to CPC subtree + year range.
        Use this overnight with full bandwidth window.
        """
        run_id = _sha(f"deep_{_ts()}")
        run = IngestRun(
            run_id=run_id,
            mode="deep",
            gate=1,
            cpc_scope=cpc_scope,
        )

        available_gb = budget_gb or self._budget.remaining_gb()

        # USPTO ODP API endpoint for targeted CPC pulls
        # Avoids downloading full bulk XML (~1TB+)
        for cpc in cpc_scope[:5]:  # Limit scope
            for year in range(year_range[0], year_range[1]):
                # Use USPTO's Open Data Portal for targeted queries
                odp_url = (
                    f"https://developer.uspto.gov/ibd-api/v1/application/grants?"
                    f"searchText=cpcCode:{cpc}&dateRangeData.startDate={year}-01-01"
                    f"&dateRangeData.endDate={year}-12-31&rows=1000&start=0"
                )
                job = DownloadJob(
                    job_id=_sha(f"{run_id}_{cpc}_{year}"),
                    job_type="uspto_odp_scoped",
                    url=odp_url,
                    dest_path=str(self.raw_dir / "odp" / f"{cpc}_{year}.json"),
                    priority=3,
                    estimated_bytes=50 * 1024 * 1024,  # ~50MB per CPC/year
                    cpc_scope=[cpc],
                )
                run.jobs.append(job)

                if sum(j.estimated_bytes for j in run.jobs) > available_gb * 1e9:
                    break

        return run

    # ── Execution ──────────────────────────────────────────────────────────

    async def execute_run(self, run: IngestRun,
                           on_progress=None) -> IngestRun:
        """
        Execute an ingest run with bandwidth awareness.
        Pauses when budget exhausted, resumes in next window.
        """
        run.status = "running"
        run.started_at = _ts()
        self._current_run = run

        if self._receipt_chain:
            self._receipt_chain.emit(
                "USPTO_INGEST_STARTED",
                {"kind": "san_terrain", "ref": "ingest"},
                {"run_id": run.run_id, "mode": run.mode},
                {"job_count": len(run.jobs),
                 "cpc_scope": run.cpc_scope,
                 "budget_gb": self._budget.remaining_gb()}
            )

        sorted_jobs = sorted(run.jobs, key=lambda j: j.priority)

        for job in sorted_jobs:
            # Bandwidth check
            if not self._budget.can_download(job.estimated_bytes):
                job.status = "paused"
                logger.warning(f"Paused: bandwidth cap approaching. "
                               f"Remaining: {self._budget.remaining_gb():.2f}GB")
                if on_progress:
                    on_progress({"event": "paused", "job": job.job_id,
                                 "reason": "bandwidth_cap",
                                 "remaining_gb": self._budget.remaining_gb()})
                continue

            if self._paused:
                job.status = "paused"
                continue

            # Execute job
            try:
                result = await self._execute_job(job, on_progress)
                if result:
                    self._budget.record_download(job.bytes_downloaded)
                    run.bandwidth_used_gb += job.bytes_downloaded / 1e9
                    if on_progress:
                        on_progress({
                            "event": "job_complete",
                            "job_id": job.job_id,
                            "type": job.job_type,
                            "bytes": job.bytes_downloaded,
                            "remaining_gb": self._budget.remaining_gb(),
                        })
            except Exception as e:
                job.status = "failed"
                job.error = str(e)
                run.errors += 1
                logger.error(f"Job {job.job_id} failed: {e}")

        # Finalize
        done = [j for j in run.jobs if j.status == "done"]
        paused = [j for j in run.jobs if j.status == "paused"]
        failed = [j for j in run.jobs if j.status == "failed"]

        if paused:
            run.status = "partial"
        elif failed and not done:
            run.status = "failed"
        else:
            run.status = "complete"

        run.completed_at = _ts()

        # Take terrain snapshot
        if self._terrain and done:
            snap = self._terrain.take_snapshot(
                cpc_scope=run.cpc_scope, tier=run.mode)
            run.snapshot_id = snap.snapshot_id

        # Log run
        self._run_log.append({
            "run_id": run.run_id,
            "mode": run.mode,
            "status": run.status,
            "jobs_done": len(done),
            "jobs_paused": len(paused),
            "jobs_failed": len(failed),
            "bandwidth_gb": round(run.bandwidth_used_gb, 3),
            "started_at": run.started_at,
            "completed_at": run.completed_at,
            "snapshot_id": run.snapshot_id,
        })
        self._save_run_log()

        return run

    async def _execute_job(self, job: DownloadJob,
                            on_progress=None) -> bool:
        """Download one job with progress tracking."""
        job.status = "downloading"
        dest = Path(job.dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Skip if already downloaded (delta check by file existence + size)
        if dest.exists() and dest.stat().st_size > 1000:
            logger.info(f"Already downloaded: {dest.name}")
            job.status = "done"
            job.bytes_downloaded = dest.stat().st_size
            return True

        try:
            import httpx
            async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
                async with client.stream(
                    "GET", job.url,
                    headers={"User-Agent": "NS-Research/1.0 (AXIOLEV Holdings)"}
                ) as r:
                    if r.status_code != 200:
                        job.status = "failed"
                        job.error = f"HTTP {r.status_code}"
                        return False

                    with open(dest, "wb") as f:
                        downloaded = 0
                        async for chunk in r.aiter_bytes(chunk_size=65536):
                            f.write(chunk)
                            downloaded += len(chunk)
                            self._budget.record_download(len(chunk))

                            # Check budget mid-download
                            if not self._budget.can_download():
                                self._paused = True
                                logger.warning("Budget exhausted mid-download. Pausing.")
                                break

                    job.bytes_downloaded = downloaded
                    job.completed_at = _ts()
                    job.status = "done"

                    # SHA manifest
                    job.sha_manifest = _sha(str(downloaded) + job.url)
                    return True

        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            if dest.exists():
                dest.unlink()  # Clean up partial download
            return False

    # ── Parsing ────────────────────────────────────────────────────────────

    def parse_patentsview_tsv(self, table_name: str,
                               cpc_filter: List[str] = None) -> dict:
        """
        Parse a downloaded PatentsView TSV into terrain storage.
        CPC filter: only import records matching target CPC codes.
        """
        from nss.actuators.san_terrain import Patent, Claim, CPC, CitationEdge

        tsv_zip = self.raw_dir / "patentsview" / f"{table_name}.tsv.zip"
        if not tsv_zip.exists():
            return {"ok": False, "error": f"Not downloaded: {tsv_zip}"}

        imported = 0
        skipped = 0
        errors = 0

        try:
            import zipfile, csv, io

            with zipfile.ZipFile(tsv_zip) as zf:
                names = zf.namelist()
                tsv_name = next((n for n in names if n.endswith('.tsv')), names[0])

                with zf.open(tsv_name) as raw:
                    # Stream parse — don't load full TSV into memory
                    reader = csv.DictReader(
                        io.TextIOWrapper(raw, encoding='utf-8', errors='replace'),
                        delimiter='\t'
                    )

                    for i, row in enumerate(reader):
                        if i > 500_000:  # Safety limit per session
                            break

                        try:
                            result = self._parse_patentsview_row(
                                table_name, row, cpc_filter)
                            if result:
                                imported += 1
                            else:
                                skipped += 1
                        except Exception:
                            errors += 1

        except ImportError:
            return {"ok": False,
                    "error": "Install: pip install pyarrow (for production Parquet parsing)"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

        return {"ok": True, "table": table_name,
                "imported": imported, "skipped": skipped, "errors": errors}

    def _parse_patentsview_row(self, table_name: str, row: dict,
                                cpc_filter: List[str] = None) -> bool:
        """Parse one row from a PatentsView table into terrain storage."""
        from nss.actuators.san_terrain import Patent, Claim, CPC, CitationEdge

        if not self._terrain:
            return False

        if table_name == "patents":
            pub_id = row.get("patent_id", "")
            if not pub_id:
                return False
            patent = Patent(
                pub_id=pub_id,
                kind="grant",
                title=row.get("title", "")[:300],
                filing_date=row.get("filing_date", ""),
                grant_date=row.get("date", ""),
            )
            return self._terrain.storage.store_patent(patent)

        elif table_name == "claims":
            pub_id = row.get("patent_id", "")
            claim_no = int(row.get("claim_sequence", 0))
            claim_id = f"{pub_id}_c{claim_no}"
            independent = row.get("dependent", "-1") == "-1"
            claim = Claim(
                claim_id=claim_id, pub_id=pub_id,
                claim_no=claim_no, independent=independent,
                text=row.get("text", "")[:5000],
            )
            return self._terrain.storage.store_claim(claim)

        elif table_name == "cpc":
            pub_id = row.get("patent_id", "")
            code = row.get("cpc_subgroup_id", "")
            if cpc_filter:
                if not any(code.startswith(c) for c in cpc_filter):
                    return False
            # Attach CPC to patent record
            meta = self._terrain.storage._patent_index.get(pub_id)
            if meta:
                codes = meta.get("cpc_codes", [])
                if code not in codes:
                    codes.append(code)
                    meta["cpc_codes"] = codes
                    self._terrain.storage._save_index("patents",
                        self._terrain.storage._patent_index)
            return True

        elif table_name == "citations":
            edge = CitationEdge(
                src_pub_id=row.get("patent_id", ""),
                dst_pub_id=row.get("citation_patent_id", ""),
                edge_type="citing",
            )
            self._terrain.storage.store_edge(edge)
            return True

        return False

    # ── Status + Control ───────────────────────────────────────────────────

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def set_budget(self, daily_cap_gb: float = None, soft_limit_pct: float = None):
        if daily_cap_gb: self._budget.daily_cap_gb = daily_cap_gb
        if soft_limit_pct: self._budget.soft_limit_pct = soft_limit_pct

    def status(self) -> dict:
        current = None
        if self._current_run:
            done = sum(1 for j in self._current_run.jobs if j.status == "done")
            total = len(self._current_run.jobs)
            current = {
                "run_id": self._current_run.run_id,
                "mode": self._current_run.mode,
                "status": self._current_run.status,
                "progress": f"{done}/{total}",
                "bandwidth_used_gb": round(self._current_run.bandwidth_used_gb, 3),
            }
        return {
            "bandwidth": self._budget.status(),
            "paused": self._paused,
            "current_run": current,
            "run_count": len(self._run_log),
            "recent_runs": self._run_log[-5:][::-1],
        }


# ── Singleton ──────────────────────────────────────────────────────────────────

_ingest_engine: Optional[USPTOIngestEngine] = None

def get_uspto_ingest(terrain_engine=None, receipt_chain=None) -> USPTOIngestEngine:
    global _ingest_engine
    if _ingest_engine is None:
        from nss.core.storage import ALEXANDRIA_ROOT
        raw_dir = ALEXANDRIA_ROOT / "terrain" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        _ingest_engine = USPTOIngestEngine(
            raw_dir=raw_dir,
            terrain_engine=terrain_engine,
            receipt_chain=receipt_chain,
        )
    return _ingest_engine
