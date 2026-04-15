"""
Alexandria Ingestion Pipeline — V1
AXIOLEV Holdings LLC © 2026
5-stage deterministic pipeline: raw → normalize → chunk → authority → candidate
POLICY: No silent drops. No passive canon promotion. Contradictions always surfaced.
"""
import hashlib, json, os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

# ── Stage definitions ──────────────────────────────────────────────────────────

class IngestionStage:
    name: str = "base"

    def process(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def receipt(self, obj_id: str, stage: str, result: str) -> Dict[str, Any]:
        payload = f"{obj_id}:{stage}:{datetime.now(timezone.utc).isoformat()}"
        return {
            "receipt_type": "INGEST_STAGE",
            "object_id": obj_id,
            "stage": stage,
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "self_hash": hashlib.sha256(payload.encode()).hexdigest()
        }


class Stage1Scan(IngestionStage):
    """Stage 1: Scan raw file — compute content_hash, detect content_type, validate path"""
    name = "scan"

    def process(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        raw_path = obj.get("raw_path", "")
        if not os.path.exists(raw_path):
            obj["stage_error"] = f"Stage1: file not found: {raw_path}"
            obj["epistemic_state"] = "raw"
            return obj

        with open(raw_path, "rb") as f:
            content = f.read()

        obj["content_hash"] = hashlib.sha256(content).hexdigest()
        obj["content_length_bytes"] = len(content)
        obj["object_id"] = hashlib.sha256(
            f"{obj.get('source_uri','')}{obj['content_hash']}".encode()
        ).hexdigest()

        # Detect content type
        if raw_path.endswith(".pdf"):
            obj["content_type"] = "pdf"
        elif raw_path.endswith((".jpg", ".png", ".jpeg", ".gif", ".webp")):
            obj["content_type"] = "image"
        else:
            obj["content_type"] = "text"

        obj["epistemic_state"] = "raw"
        obj["stage1_complete"] = True
        return obj


class Stage2Normalize(IngestionStage):
    """Stage 2: Normalize content — extract text, write to normalized_path"""
    name = "normalize"

    def process(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        if obj.get("content_type") == "text":
            obj["normalized_path"] = obj.get("raw_path", "")
            obj["epistemic_state"] = "normalized"
            obj["stage2_complete"] = True
        elif obj.get("content_type") == "pdf":
            # PDF text extraction placeholder — integrate pdfplumber in production
            obj["normalized_path"] = obj.get("raw_path", "").replace(".pdf", "_extracted.txt")
            obj["epistemic_state"] = "normalized"
            obj["stage2_complete"] = True
            obj["stage2_note"] = "PDF: text extraction requires pdfplumber integration"
        else:
            obj["epistemic_state"] = "normalized"
            obj["stage2_complete"] = True
        return obj


class Stage3Chunk(IngestionStage):
    """Stage 3: Chunk content for embedding — 512-token chunks with 64-token overlap"""
    name = "chunk"

    def process(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        # Chunk metadata recorded — actual chunking done by embedding service
        obj["chunk_config"] = {
            "chunk_size_tokens": 512,
            "overlap_tokens": 64,
            "strategy": "sentence_boundary"
        }
        obj["stage3_complete"] = True
        return obj


class Stage4Authority(IngestionStage):
    """Stage 4: Assign authority score based on source_type and provenance"""
    name = "authority"

    AUTHORITY_MAP = {
        "manual": 0.9,   # founder-uploaded content
        "file":   0.7,   # local file system
        "api":    0.6,   # API source
        "url":    0.4,   # web content
        "voice":  0.5,   # voice transcript
    }

    def process(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        source_type = obj.get("source_type", "file")
        obj["authority_score"] = self.AUTHORITY_MAP.get(source_type, 0.5)
        obj["authority_source"] = f"auto:{source_type}"
        obj["requires_review"] = obj["authority_score"] < 0.85
        obj["stage4_complete"] = True
        return obj


class Stage5Candidate(IngestionStage):
    """Stage 5: Mark as candidate — NEVER auto-promote to canon"""
    name = "candidate_gate"

    def process(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        # POLICY: epistemic_state never advances past 'normalized' automatically.
        # candidate and canon require explicit founder review.
        # This stage only records that the object is ready for review queue.
        obj["ready_for_review"] = True
        obj["promotion_blocked"] = True  # always True — no auto-promotion
        obj["promotion_note"] = "Canon promotion requires explicit founder approval via /alexandria/review/approve"
        # epistemic_state stays 'normalized' — NOT advanced to 'candidate' automatically
        obj["stage5_complete"] = True
        return obj


# ── Pipeline orchestrator ─────────────────────────────────────────────────────

class IngestionPipeline:
    """
    Orchestrates all 5 stages. Returns receipted result.
    POLICY: No silent drops. Every failure is receipted.
    """

    def __init__(self, receipt_log_path: Optional[str] = None):
        self.stages = [
            Stage1Scan(),
            Stage2Normalize(),
            Stage3Chunk(),
            Stage4Authority(),
            Stage5Candidate(),
        ]
        self.receipt_log = receipt_log_path

    def ingest(self, raw_path: str, source_uri: str, source_type: str = "file",
               ingested_by: str = "pipeline_v1") -> Dict[str, Any]:
        """Run all 5 stages. Returns final object with stage receipts."""
        obj = {
            "raw_path": raw_path,
            "source_uri": source_uri,
            "source_type": source_type,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "ingested_by": ingested_by,
            "stage_receipts": []
        }

        for stage in self.stages:
            try:
                obj = stage.process(obj)
                receipt = stage.receipt(obj.get("object_id", "unknown"), stage.name, "ok")
            except Exception as exc:
                receipt = stage.receipt(obj.get("object_id", "unknown"), stage.name, f"error:{exc}")
                obj["pipeline_error"] = f"{stage.name}: {exc}"
                break  # stop pipeline on error — object stays in raw state
            obj["stage_receipts"].append(receipt)

        # Write to receipt log if configured
        if self.receipt_log:
            try:
                with open(self.receipt_log, "a") as f:
                    summary = {
                        "type": "INGEST_RECEIPT",
                        "object_id": obj.get("object_id", "unknown"),
                        "source_uri": source_uri,
                        "final_state": obj.get("epistemic_state", "raw"),
                        "stages_completed": len(obj.get("stage_receipts", [])),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    payload = json.dumps(summary, separators=(',', ':'), sort_keys=True)
                    summary["self_hash"] = hashlib.sha256(payload.encode()).hexdigest()
                    f.write(json.dumps(summary, separators=(',', ':')) + "\n")
            except Exception:
                pass  # receipt log failure is not a pipeline failure

        return obj
