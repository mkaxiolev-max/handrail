#!/usr/bin/env python3
"""
Alexandria Full Ingest Script
Crawls /Volumes/NSExternal/alexandria and /Volumes/NSExternal/ether-storage
and ingests everything into NS ether store.

Run from NSS 2 root:
  source .venv/bin/activate && python3 scripts/ingest_alexandria.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from nss.core.receipts import ReceiptChain
from nss.jobs.ingest_watcher import get_ingest_engine

PATHS = [
    "/Volumes/NSExternal/alexandria",
    "/Volumes/NSExternal/ether-storage",
    "/Volumes/NSExternal/ns_home",
]

INGEST_EXTENSIONS = {
    ".md", ".txt", ".pdf", ".json", ".yaml", ".yml",
    ".py", ".js", ".ts", ".html", ".csv", ".rst",
    ".docx", ".xlsx", ".pptx"
}

def run():
    print("=" * 60)
    print("⚡ ALEXANDRIA FULL INGEST")
    print("=" * 60)

    rc = ReceiptChain()
    engine = get_ingest_engine(rc)

    total_files = 0
    total_ingested = 0
    total_skipped = 0
    total_errors = 0

    for base_path in PATHS:
        p = Path(base_path)
        if not p.exists():
            print(f"  ⚠  Skipping (not found): {base_path}")
            continue

        print(f"\n→ Scanning: {base_path}")
        files = [f for f in p.rglob("*") if f.is_file()]
        print(f"  Found {len(files)} files")

        for f in files:
            total_files += 1
            if f.suffix.lower() not in INGEST_EXTENSIONS:
                total_skipped += 1
                continue
            try:
                result = engine.ingest_file(str(f))
                if result.get("status") in ("ok", "ingested"):
                    total_ingested += 1
                    print(f"  ✓ {f.name}")
                elif result.get("status") == "duplicate":
                    total_skipped += 1
                else:
                    total_errors += 1
                    print(f"  ✗ {f.name}: {result.get('error','unknown')}")
            except Exception as e:
                total_errors += 1
                print(f"  ✗ {f.name}: {str(e)[:60]}")

    print("\n" + "=" * 60)
    print(f"  Total scanned:  {total_files}")
    print(f"  Ingested:       {total_ingested}")
    print(f"  Skipped:        {total_skipped}")
    print(f"  Errors:         {total_errors}")
    print("=" * 60)
    rc.emit("ALEXANDRIA_FULL_INGEST", {"kind": "system", "ref": "ingest"},
            {"ingested": total_ingested, "errors": total_errors}, {})
    print("✓ Done. Check console Alexandria tab for doc count.")

if __name__ == "__main__":
    run()
