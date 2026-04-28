from __future__ import annotations
import hashlib, logging, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
import requests

logger = logging.getLogger(__name__)
USPTO_GRANTS_INDEX = "https://bulkdata.uspto.gov/data/patent/grant/redbook/fulltext"
USER_AGENT = "AXIOLEV-NS-RIS/1.0 (research; contact: ops@axiolev.com)"


def list_weekly_files(weeks_back: int = 12) -> list[dict]:
    today = datetime.now(timezone.utc).date()
    days_back = (today.weekday() - 1) % 7
    last_tuesday = today - timedelta(days=days_back)
    candidates = []
    for i in range(weeks_back):
        tuesday = last_tuesday - timedelta(weeks=i)
        fname = f"ipg{tuesday.strftime('%y%m%d')}.zip"
        url = f"{USPTO_GRANTS_INDEX}/{tuesday.year}/{fname}"
        candidates.append({"url": url, "filename": fname, "week_of": tuesday.isoformat()})
    return candidates


def fetch_file(url: str, dest_dir: Path, timeout: int = 600, max_retries: int = 5) -> dict:
    dest_dir.mkdir(parents=True, exist_ok=True)
    fname = url.rsplit("/", 1)[-1]
    dest = dest_dir / fname
    if dest.exists() and dest.stat().st_size > 1_000_000:
        sha = _sha256_file(dest)
        return {"url": url, "path": str(dest), "size": dest.stat().st_size,
                "sha256": sha, "cached": True, "ts": datetime.now(timezone.utc).isoformat()}
    last_err = None
    for attempt in range(max_retries):
        try:
            with requests.get(url, stream=True, timeout=timeout,
                              headers={"User-Agent": USER_AGENT}) as r:
                if r.status_code == 404:
                    return {"url": url, "path": None, "size": 0, "sha256": None,
                            "cached": False, "missing": True,
                            "ts": datetime.now(timezone.utc).isoformat()}
                r.raise_for_status()
                tmp = dest.with_suffix(".part")
                size = 0
                with tmp.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=1 << 20):
                        if chunk:
                            f.write(chunk); size += len(chunk)
                tmp.rename(dest)
                return {"url": url, "path": str(dest), "size": size,
                        "sha256": _sha256_file(dest), "cached": False,
                        "ts": datetime.now(timezone.utc).isoformat()}
        except Exception as e:
            last_err = str(e); wait = 2 ** attempt
            logger.warning(f"fetch attempt {attempt+1} failed: {e}; sleep {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"fetch failed after {max_retries} attempts: {last_err}")


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
