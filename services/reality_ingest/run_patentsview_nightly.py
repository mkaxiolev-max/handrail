"""Source-adaptive PatentsView ingest. Replaces dead bulkdata.uspto.gov path."""
from __future__ import annotations
import argparse, json, logging, os, signal, sys, time, uuid, hashlib
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import orjson

from services.reality_ingest.schema import (
    SourceLane, SourceTier, EpistemicClass, IngestionReceipt,
)
from services.reality_ingest.source_resolver import USPTOSourceResolver, ResolverConfig
from services.reality_ingest.patentsview import parse, normalize, score
from services.reality_ingest.uspto.persist import _atomic_write
from services.reality_ingest.uspto.contradiction import ContradictionLane


def setup_logging(log_dir: Path, run_id: str):
    log_dir.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(log_dir / f"{run_id}.log")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[fh, sh], force=True)


def heartbeat(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_bytes(orjson.dumps(payload))
    tmp.rename(path)


def disk_free_gb(path: Path) -> int:
    st = os.statvfs(path)
    return (st.f_bavail * st.f_frsize) // (1 << 30)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ext-root", type=Path, default=Path("/Volumes/NSExternal/ris/uspto"))
    ap.add_argument("--int-root", type=Path, default=Path.home() / "axiolev_runtime/.run/ris_uspto")
    ap.add_argument("--max-records", type=int, default=None)
    ap.add_argument("--tables", nargs="+",
                    default=["patent_application", "patent_assignee",
                             "patent_inventor", "patent_cpc",
                             "patent_figures", "patent",
                             "patent_us_citation"])
    args = ap.parse_args()

    run_id = f"ris_pv_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    log = logging.getLogger("ris.pv")
    setup_logging(args.ext_root / "logs", run_id)
    log.info(f"=== RIS PatentsView (source-adaptive) {run_id} ===")

    raw_dir       = args.ext_root / "raw" / "patentsview"
    norm_ext      = args.ext_root / "normalized"
    norm_int      = args.int_root / "normalized"
    receipts      = args.ext_root / "receipts"
    source_rec    = args.ext_root / "source_receipts"
    drift_log     = args.ext_root / "drift_log"
    contra_path   = args.ext_root / "contradictions" / f"{run_id}.jsonl"
    state_path    = args.int_root / "state.json"
    hb_path       = args.int_root / "heartbeat.json"
    summary_path  = args.ext_root / "summaries" / f"{run_id}.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    resolver = USPTOSourceResolver(ResolverConfig(
        receipts_dir=source_rec, drift_log_dir=drift_log,
    ))
    log.info(f"resolver lanes: {[l.value for l in resolver.config.lane_priority]}")

    snap = resolver.status_snapshot()
    for lane, info in snap.items():
        log.info(f"  lane {lane}: avail={info['available']} tier={info['tier']} "
                 f"reason={info.get('reason','')}")

    halt = {"flag": False}
    def _sig(*_):
        halt["flag"] = True
        log.warning("shutdown signal received")
    signal.signal(signal.SIGTERM, _sig)
    signal.signal(signal.SIGINT, _sig)

    contra = ContradictionLane(contra_path)
    totals = {
        "tables_attempted": 0, "tables_succeeded": 0,
        "rows_parsed": 0, "rows_normalized": 0, "rows_persisted": 0,
        "edges_emitted": 0, "errors": [],
        "by_lane": defaultdict(int), "by_table": {}, "drift_events": 0,
    }
    started = time.time()

    aux_index = {
        "assignees": defaultdict(list),
        "inventors": defaultdict(list),
        "cpc":       defaultdict(list),
        "citations": defaultdict(list),
    }

    def fetch_via_resolver(table: str):
        log.info(f"  resolving {table}...")
        result = resolver.resolve(table)
        if not result.success:
            raise RuntimeError(f"all lanes failed for {table}; receipt {result.receipt_id}")
        if result.drift_detected:
            totals["drift_events"] += 1
            log.warning(f"  drift: {result.drift_notes}")
        log.info(f"  resolved via {result.chosen_lane.value} (tier={result.chosen_tier.value})")
        lane = resolver.lanes[result.chosen_lane]
        meta_fetch = lane.fetch(table, raw_dir)
        log.info(f"  {meta_fetch.get('url', table)}: {meta_fetch['size']/1e6:.1f}MB"
                 + (" (cached)" if meta_fetch.get("cached") else ""))
        return Path(meta_fetch["path"]), {
            "url": meta_fetch.get("url", ""),
            "source_receipt_id": result.receipt_id,
            "lane": result.chosen_lane,
        }

    # Pass 1: aux tables
    for table in [t for t in args.tables if t != "patent"]:
        if halt["flag"] or disk_free_gb(args.ext_root) < 5:
            break
        totals["tables_attempted"] += 1
        try:
            zip_path, meta = fetch_via_resolver(table)
        except Exception as e:
            totals["errors"].append(f"fetch:{table}:{e}")
            log.error(f"  {table} fetch failed: {e}")
            continue

        log.info(f"  indexing {table}...")
        rows = 0
        for row in parse.stream_tsv_from_zip(zip_path):
            rows += 1
            pid = row.get("patent_id") or row.get("id")
            if not pid: continue
            if table == "patent_assignee":
                org = row.get("disambig_assignee_organization") or row.get("organization")
                ind = row.get("disambig_assignee_individual_name_first")
                if org: aux_index["assignees"][pid].append(org)
                elif ind: aux_index["assignees"][pid].append(ind)
            elif table == "patent_inventor":
                first = row.get("disambig_inventor_name_first") or ""
                last  = row.get("disambig_inventor_name_last") or ""
                name = f"{first} {last}".strip()
                if name: aux_index["inventors"][pid].append(name)
            elif table == "patent_cpc":
                code = ((row.get("cpc_section") or "") + (row.get("cpc_class") or "") +
                        (row.get("cpc_subclass") or "") + (row.get("cpc_group") or "") +
                        "/" + (row.get("cpc_subgroup") or "")).strip("/")
                if code: aux_index["cpc"][pid].append(code)
            elif table == "patent_us_citation":
                cited = row.get("citation_patent_id") or row.get("citation_id")
                if cited: aux_index["citations"][pid].append(cited)
            if rows % 250_000 == 0:
                log.info(f"    {table}: {rows:,} rows indexed")
            if halt["flag"]: break
        totals["by_table"][table] = rows
        totals["tables_succeeded"] += 1
        log.info(f"  {table}: {rows:,} rows indexed")

    # Pass 2: patent table with join
    if "patent" in args.tables and not halt["flag"]:
        totals["tables_attempted"] += 1
        try:
            zip_path, meta = fetch_via_resolver("patent")
        except Exception as e:
            log.error(f"patent fetch failed: {e}")
            contra.close()
            return _emit_summary(summary_path, run_id, totals, started, log)

        log.info("normalizing patents...")
        for row in parse.stream_tsv_from_zip(zip_path):
            if halt["flag"]: break
            if args.max_records and totals["rows_persisted"] >= args.max_records: break
            totals["rows_parsed"] += 1
            pid = row.get("patent_id") or row.get("id")
            if not pid: continue
            obj = normalize.normalize_patent_row(
                row, source_url=meta["url"],
                source_receipt_id=meta["source_receipt_id"],
                ingestion_receipt_id=f"INGEST-{uuid.uuid4().hex[:12]}",
                join={
                    "assignees": aux_index["assignees"].get(pid, []),
                    "inventors": aux_index["inventors"].get(pid, []),
                    "cpc":       aux_index["cpc"].get(pid, []),
                    "citations": aux_index["citations"].get(pid, []),
                },
            )
            if not obj: continue
            obj = score.score(obj)
            totals["rows_normalized"] += 1
            d = (obj.grant_date or datetime.now(timezone.utc)).strftime("%Y/%m/%d")
            body = obj.canonical_bytes()
            sha = hashlib.sha256(body).hexdigest()
            _atomic_write(norm_ext / d / f"{obj.id}.json", body)
            _atomic_write(norm_int / d / f"{obj.id}.json", body)
            ireceipt = IngestionReceipt(
                receipt_id=f"RCT-{obj.id}-{int(time.time())}",
                object_id=obj.id, source="USPTO",
                source_lane=obj.source_lane,
                source_receipt_id=obj.source_receipt_id,
                epistemic_class=obj.epistemic_class,
                raw_sha256=sha, normalized_sha256=sha,
                fetch_receipt_id=meta["source_receipt_id"],
                parse_receipt_id=f"PARSE-{uuid.uuid4().hex[:8]}",
                normalize_receipt_id=f"NORM-{uuid.uuid4().hex[:8]}",
                score_receipt_id=f"SCORE-{uuid.uuid4().hex[:8]}",
                persist_receipt_id=f"PERSIST-{uuid.uuid4().hex[:8]}",
                timestamp=datetime.now(timezone.utc),
            )
            _atomic_write(receipts / d / f"{obj.id}.receipt.json",
                          orjson.dumps(ireceipt.model_dump(mode="json"), option=orjson.OPT_INDENT_2))
            edges = contra.check(obj)
            totals["rows_persisted"] += 1
            totals["edges_emitted"] += len(edges)
            totals["by_lane"][obj.source_lane.value] += 1
            if totals["rows_persisted"] % 1000 == 0:
                elapsed = time.time() - started
                rate = totals["rows_persisted"] / elapsed if elapsed > 0 else 0
                heartbeat(hb_path, {
                    "run_id": run_id, "ts": datetime.now(timezone.utc).isoformat(),
                    "rows_persisted": totals["rows_persisted"],
                    "rows_parsed": totals["rows_parsed"],
                    "rate_per_sec": round(rate, 2), "elapsed_s": int(elapsed),
                    "by_lane": dict(totals["by_lane"]),
                })
        totals["tables_succeeded"] += 1

    contra.close()
    return _emit_summary(summary_path, run_id, totals, started, log)


def _emit_summary(summary_path, run_id, totals, started, log):
    elapsed = time.time() - started
    summary = {
        "run_id": run_id, "pipeline": "patentsview-source-adaptive",
        "started_at": datetime.fromtimestamp(started, tz=timezone.utc).isoformat(),
        "ended_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_s": int(elapsed),
        "totals": {**totals, "by_lane": dict(totals.get("by_lane", {}))},
    }
    summary_path.write_bytes(orjson.dumps(summary, option=orjson.OPT_INDENT_2))
    log.info("=" * 60)
    log.info(f"SUMMARY: rows_persisted={totals['rows_persisted']:,} "
             f"edges={totals['edges_emitted']:,} elapsed={elapsed/3600:.2f}h")
    log.info(f"  by_lane: {dict(totals.get('by_lane', {}))}")
    log.info("=" * 60)
    return 0 if not totals["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
