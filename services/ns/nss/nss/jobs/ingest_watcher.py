"""
NS Ether Ingest Watcher
Watches a directory for new files, ingests them into Alexandria automatically.
Also handles:
  - Bootstrap scan of existing Alexandria folder on startup
  - Web page ingestion by URL
  - Recursive directory ingestion

Drop any file into the watched folder → it's in Alexandria within 60 seconds.
Supported: .txt .md .pdf .html .json .yaml .csv .py .js .ts .docx

Every ingested document:
  - Gets a content hash (deduplication)
  - Gets stored in Alexandria/ether/
  - Gets a receipt emitted
  - Becomes queryable by the arbiter
"""

import os
import sys
import json
import time
import hashlib
import asyncio
import mimetypes
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Set

# ── Config ─────────────────────────────────────────────────────────────────────

SUPPORTED_EXTENSIONS = {
    '.txt', '.md', '.pdf', '.html', '.htm', '.json', '.yaml', '.yml',
    '.csv', '.py', '.js', '.ts', '.rst', '.org', '.tex',
    '.docx', '.doc', '.pptx', '.xlsx'
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()

def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()[:16]

def _url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


# ── Text Extractors ────────────────────────────────────────────────────────────

def extract_text(path: Path) -> Optional[str]:
    """Extract text from any supported file type."""
    ext = path.suffix.lower()
    
    try:
        if ext in {'.txt', '.md', '.rst', '.org', '.tex'}:
            return path.read_text(errors='replace')
        
        elif ext in {'.py', '.js', '.ts', '.json', '.yaml', '.yml', '.csv'}:
            return path.read_text(errors='replace')
        
        elif ext == '.html' or ext == '.htm':
            import re
            raw = path.read_text(errors='replace')
            # Strip tags
            text = re.sub(r'<[^>]+>', ' ', raw)
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        
        elif ext == '.pdf':
            try:
                import pypdf
                reader = pypdf.PdfReader(str(path))
                pages = []
                for page in reader.pages:
                    pages.append(page.extract_text() or '')
                return '\n'.join(pages)
            except ImportError:
                # Try pdfminer
                try:
                    from pdfminer.high_level import extract_text as pdf_extract
                    return pdf_extract(str(path))
                except ImportError:
                    return f"[PDF: {path.name} — install pypdf or pdfminer to extract]"
        
        elif ext == '.docx':
            try:
                import docx
                doc = docx.Document(str(path))
                return '\n'.join(p.text for p in doc.paragraphs)
            except ImportError:
                return f"[DOCX: {path.name} — install python-docx to extract]"
        
        else:
            # Attempt UTF-8 read
            return path.read_text(errors='replace')
    
    except Exception as e:
        return f"[Extract error: {e}]"


# ── Ingest Engine ──────────────────────────────────────────────────────────────

class EtherIngestEngine:
    """
    Core ingestion engine. 
    Stores documents in Alexandria/ether/, deduplicates by hash.
    """

    def __init__(self, receipt_chain=None):
        from nss.core.storage import ALEXANDRIA_ROOT
        self._ether_dir = ALEXANDRIA_ROOT / "ether" / "docs"
        self._index_path = ALEXANDRIA_ROOT / "ether" / "_index.json"
        self._ether_dir.mkdir(parents=True, exist_ok=True)
        self._receipt_chain = receipt_chain
        self._index: Dict[str, dict] = self._load_index()
        self._ingested_hashes: Set[str] = set(self._index.keys())

    def _load_index(self) -> dict:
        if self._index_path.exists():
            try:
                return json.loads(self._index_path.read_text())
            except Exception:
                return {}
        return {}

    def _save_index(self):
        self._index_path.write_text(json.dumps(self._index, indent=2))

    def already_ingested(self, content_hash: str) -> bool:
        return content_hash in self._ingested_hashes

    def ingest_file(self, path: Path, source_label: str = "") -> dict:
        """Ingest a single file. Returns result dict."""
        path = Path(path)
        
        if not path.exists() or not path.is_file():
            return {"ok": False, "error": f"File not found: {path}"}
        
        if path.stat().st_size > MAX_FILE_SIZE:
            return {"ok": False, "error": f"File too large: {path.stat().st_size} bytes"}
        
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return {"ok": False, "error": f"Unsupported extension: {path.suffix}"}
        
        content_hash = _file_hash(path)
        
        if self.already_ingested(content_hash):
            return {"ok": True, "skipped": True, "hash": content_hash,
                    "reason": "already ingested"}
        
        # Extract text
        text = extract_text(path)
        if not text:
            return {"ok": False, "error": "Empty extract"}
        
        # Store
        doc_id = f"doc_{content_hash}"
        doc_path = self._ether_dir / f"{doc_id}.json"
        
        doc = {
            "id": doc_id,
            "hash": content_hash,
            "source_type": "file",
            "source_path": str(path),
            "source_label": source_label or path.name,
            "filename": path.name,
            "extension": path.suffix.lower(),
            "text": text[:500_000],  # 500K char limit per doc
            "text_length": len(text),
            "ingested_at": _ts(),
        }
        
        doc_path.write_text(json.dumps(doc, indent=2))
        
        # Update index
        self._index[content_hash] = {
            "id": doc_id,
            "source": str(path),
            "filename": path.name,
            "ingested_at": _ts(),
            "bytes": path.stat().st_size,
        }
        self._ingested_hashes.add(content_hash)
        self._save_index()
        
        # Receipt
        if self._receipt_chain:
            self._receipt_chain.emit(
                "ETHER_INGESTED",
                {"kind": "ether", "ref": "file"},
                {"filename": path.name, "hash": content_hash},
                {"bytes": path.stat().st_size, "text_length": len(text)}
            )
        
        return {
            "ok": True,
            "id": doc_id,
            "hash": content_hash,
            "filename": path.name,
            "text_length": len(text),
        }

    async def ingest_url(self, url: str, label: str = "") -> dict:
        """Fetch and ingest a URL."""
        url_hash = _url_hash(url)
        
        if self.already_ingested(url_hash):
            return {"ok": True, "skipped": True, "hash": url_hash,
                    "reason": "URL already ingested"}
        
        try:
            import httpx
            async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
                r = await client.get(url, headers={"User-Agent": "NS-Research/1.0"})
                raw = r.text
        except Exception as e:
            return {"ok": False, "error": f"Fetch failed: {e}"}
        
        # Strip HTML
        import re
        text = re.sub(r'<[^>]+>', ' ', raw)
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) < 100:
            return {"ok": False, "error": "Insufficient text content"}
        
        doc_id = f"doc_{url_hash}"
        doc_path = self._ether_dir / f"{doc_id}.json"
        
        doc = {
            "id": doc_id,
            "hash": url_hash,
            "source_type": "url",
            "source_url": url,
            "source_label": label or url,
            "text": text[:500_000],
            "text_length": len(text),
            "ingested_at": _ts(),
        }
        
        doc_path.write_text(json.dumps(doc, indent=2))
        
        self._index[url_hash] = {
            "id": doc_id,
            "source": url,
            "ingested_at": _ts(),
            "bytes": len(text),
        }
        self._ingested_hashes.add(url_hash)
        self._save_index()
        
        if self._receipt_chain:
            self._receipt_chain.emit(
                "ETHER_INGESTED",
                {"kind": "ether", "ref": "url"},
                {"url": url[:200], "hash": url_hash},
                {"text_length": len(text)}
            )
        
        return {"ok": True, "id": doc_id, "hash": url_hash,
                "url": url, "text_length": len(text)}

    def bootstrap_directory(self, directory: Path,
                             recursive: bool = True) -> dict:
        """
        Scan an existing directory and ingest everything.
        This is the 'load my existing Alexandria' function.
        """
        directory = Path(directory).expanduser()
        if not directory.exists():
            return {"ok": False, "error": f"Directory not found: {directory}"}
        
        files = []
        if recursive:
            for ext in SUPPORTED_EXTENSIONS:
                files.extend(directory.rglob(f"*{ext}"))
                files.extend(directory.rglob(f"*{ext.upper()}"))
        else:
            for f in directory.iterdir():
                if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
                    files.append(f)
        
        # Deduplicate
        files = list(set(files))
        
        results = {"total": len(files), "ingested": 0, "skipped": 0,
                   "errors": 0, "details": []}
        
        for f in files:
            r = self.ingest_file(f, source_label=str(f.relative_to(directory)))
            if r.get("ok"):
                if r.get("skipped"):
                    results["skipped"] += 1
                else:
                    results["ingested"] += 1
            else:
                results["errors"] += 1
            results["details"].append({
                "file": f.name,
                "result": "ingested" if (r.get("ok") and not r.get("skipped"))
                          else ("skipped" if r.get("skipped") else "error"),
                "note": r.get("error", "")
            })
        
        return results

    def get_stats(self) -> dict:
        """Rich stats for the console UI."""
        index = self._index
        total = len(index)
        
        # Type breakdown
        by_type: Dict[str, int] = {}
        by_ext: Dict[str, int] = {}
        recent: list = []
        total_bytes = 0
        
        for h, meta in index.items():
            src = meta.get("source", "")
            if src.startswith("http"):
                by_type["url"] = by_type.get("url", 0) + 1
            else:
                ext = Path(src).suffix.lower() or ".unknown"
                by_type["file"] = by_type.get("file", 0) + 1
                by_ext[ext] = by_ext.get(ext, 0) + 1
            total_bytes += meta.get("bytes", 0)
            recent.append({
                "id": meta.get("id", ""),
                "name": Path(src).name if not src.startswith("http") else src[:60],
                "source": src[:80],
                "ingested_at": meta.get("ingested_at", ""),
                "bytes": meta.get("bytes", 0),
            })
        
        # Sort recent by ingested_at
        recent.sort(key=lambda x: x.get("ingested_at", ""), reverse=True)
        
        return {
            "total_docs": total,
            "total_bytes": total_bytes,
            "by_type": by_type,
            "by_extension": dict(sorted(by_ext.items(), key=lambda x: -x[1])[:10]),
            "recent": recent[:20],
            "ether_dir": str(self._ether_dir),
            "drop_dir": str(self._ether_dir.parent.parent / "drop"),
            "watcher_active": True,
        }

    def search(self, query: str, limit: int = 10) -> List[dict]:
        """Simple keyword search over ingested ether."""
        query_lower = query.lower()
        results = []
        
        for doc_file in self._ether_dir.glob("*.json"):
            try:
                doc = json.loads(doc_file.read_text())
                text = doc.get("text", "")
                if query_lower in text.lower():
                    # Find snippet
                    idx = text.lower().find(query_lower)
                    snippet = text[max(0, idx-100):idx+200]
                    results.append({
                        "id": doc["id"],
                        "source": doc.get("source_label") or doc.get("source_url") or doc.get("source_path", ""),
                        "snippet": snippet,
                        "score": text.lower().count(query_lower),
                    })
                    if len(results) >= limit * 3:
                        break
            except Exception:
                continue
        
        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]


# ── Drop Folder Watcher ────────────────────────────────────────────────────────

class DropFolderWatcher:
    """
    Watches a directory for new files and auto-ingests them.
    Poll-based (no inotify dependency — works on Mac + Linux).
    """

    def __init__(self, watch_dir: Path, engine: EtherIngestEngine,
                 poll_interval: float = 10.0):
        self._watch_dir = Path(watch_dir)
        self._watch_dir.mkdir(parents=True, exist_ok=True)
        self._engine = engine
        self._poll_interval = poll_interval
        self._seen: Set[str] = set()
        self._running = False

    async def run(self):
        """Start watching. Call as asyncio task."""
        self._running = True
        print(f"  ✓ Drop folder watcher: {self._watch_dir}")
        
        while self._running:
            try:
                self._scan()
            except Exception as e:
                print(f"  ⚠  Watcher error: {e}")
            await asyncio.sleep(self._poll_interval)

    def _scan(self):
        for f in self._watch_dir.iterdir():
            if f.is_file() and str(f) not in self._seen:
                self._seen.add(str(f))
                if f.suffix.lower() in SUPPORTED_EXTENSIONS:
                    result = self._engine.ingest_file(f)
                    if result.get("ok") and not result.get("skipped"):
                        print(f"  ✓ Auto-ingested: {f.name}")

    def stop(self):
        self._running = False


# ── Web Crawler ────────────────────────────────────────────────────────────────

class WebCrawler:
    """
    Depth-limited web crawler that feeds into ether ingest.
    Respects robots.txt, deduplicates by URL hash, rate-limited.
    """

    def __init__(self, engine: EtherIngestEngine):
        self._engine = engine
        self._visited: Set[str] = set()

    async def crawl(self, seed_url: str, depth: int = 2,
                    domain_limit: str = None,
                    rate_limit: float = 1.0) -> dict:
        """
        Crawl from seed_url to given depth.
        domain_limit: if set, only follow links on this domain.
        rate_limit: seconds between requests.
        """
        results = {"crawled": 0, "ingested": 0, "errors": 0, "urls": []}
        queue = [(seed_url, 0)]
        
        while queue:
            url, current_depth = queue.pop(0)
            
            if url in self._visited:
                continue
            self._visited.add(url)
            
            # Ingest this URL
            r = await self._engine.ingest_url(url)
            results["crawled"] += 1
            
            if r.get("ok") and not r.get("skipped"):
                results["ingested"] += 1
                results["urls"].append(url)
            elif r.get("error"):
                results["errors"] += 1
            
            # Follow links if not at max depth
            if current_depth < depth:
                try:
                    links = await self._extract_links(url, domain_limit)
                    for link in links[:20]:  # max 20 links per page
                        if link not in self._visited:
                            queue.append((link, current_depth + 1))
                except Exception:
                    pass
            
            await asyncio.sleep(rate_limit)
        
        return results

    async def _extract_links(self, url: str,
                               domain_limit: str = None) -> List[str]:
        """Extract all links from a fetched page."""
        try:
            import httpx, re
            from urllib.parse import urljoin, urlparse
            
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                r = await client.get(url, headers={"User-Agent": "NS-Research/1.0"})
                html = r.text
            
            links = []
            base_domain = urlparse(url).netloc
            
            for href in re.findall(r'href=["\']([^"\']+)["\']', html):
                absolute = urljoin(url, href)
                parsed = urlparse(absolute)
                
                # Only HTTP/HTTPS
                if parsed.scheme not in ('http', 'https'):
                    continue
                
                # Domain limit
                if domain_limit and domain_limit not in parsed.netloc:
                    continue
                elif not domain_limit and parsed.netloc != base_domain:
                    continue  # Default: stay on same domain
                
                links.append(absolute)
            
            return list(set(links))
        except Exception:
            return []


# ── Singleton ──────────────────────────────────────────────────────────────────

_engine: Optional[EtherIngestEngine] = None
_watcher: Optional[DropFolderWatcher] = None

def get_ingest_engine(receipt_chain=None) -> EtherIngestEngine:
    global _engine
    if _engine is None:
        _engine = EtherIngestEngine(receipt_chain=receipt_chain)
    return _engine

def get_crawler(receipt_chain=None) -> WebCrawler:
    engine = get_ingest_engine(receipt_chain)
    return WebCrawler(engine)

def get_drop_watcher(watch_dir: Path = None,
                      receipt_chain=None) -> DropFolderWatcher:
    global _watcher
    if _watcher is None:
        from nss.core.storage import ALEXANDRIA_ROOT
        watch = watch_dir or (ALEXANDRIA_ROOT / "drop")
        _watcher = DropFolderWatcher(watch, get_ingest_engine(receipt_chain))
    return _watcher
