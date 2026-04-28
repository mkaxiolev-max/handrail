"""USPTOSourceResolver. Tries lanes in priority order, records the chain."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from uuid import uuid4
import logging
import orjson

from services.reality_ingest.schema import (
    SourceLane, SourceTier, SourceCandidate, SourceResolutionResult,
)
from .lanes import SourceLaneAdapter, PatentsViewS3Lane, USPTOODPApiLane, LocalInboxLane

logger = logging.getLogger(__name__)


@dataclass
class ResolverConfig:
    receipts_dir: Path
    drift_log_dir: Path
    lane_priority: List[SourceLane] = field(default_factory=lambda: [
        SourceLane.USPTO_ODP_API,
        SourceLane.PATENTSVIEW_S3,
        SourceLane.LOCAL_INBOX,
    ])
    require_authoritative_for: List[str] = field(default_factory=list)


class USPTOSourceResolver:
    def __init__(self, config: ResolverConfig):
        self.config = config
        self.lanes = {
            SourceLane.USPTO_ODP_API:   USPTOODPApiLane(),
            SourceLane.PATENTSVIEW_S3:  PatentsViewS3Lane(),
            SourceLane.LOCAL_INBOX:     LocalInboxLane(),
        }
        self.config.receipts_dir.mkdir(parents=True, exist_ok=True)
        self.config.drift_log_dir.mkdir(parents=True, exist_ok=True)

    def resolve(self, target: str,
                require_tier: Optional[SourceTier] = None) -> SourceResolutionResult:
        rid = f"SRR-{uuid4().hex[:12]}"
        candidates: List[SourceCandidate] = []
        chosen: Optional[SourceCandidate] = None
        drift_detected = False
        drift_notes: List[str] = []

        for lane_kind in self.config.lane_priority:
            lane = self.lanes[lane_kind]
            cand = lane.candidate(target)
            candidates.append(cand)
            drift = self._check_drift(lane_kind, cand.available)
            if drift:
                drift_detected = True
                drift_notes.append(drift)
            if not cand.available:
                continue
            if require_tier and not _tier_ge(cand.tier, require_tier):
                continue
            chosen = cand
            break

        result = SourceResolutionResult(
            receipt_id=rid,
            timestamp=datetime.now(timezone.utc),
            target=target,
            candidates_tried=candidates,
            chosen=chosen,
            chosen_lane=chosen.lane if chosen else SourceLane.UNAVAILABLE,
            chosen_tier=chosen.tier if chosen else SourceTier.UNVERIFIED,
            success=chosen is not None,
            drift_detected=drift_detected,
            drift_notes=drift_notes,
        )
        self._write_receipt(result)
        if drift_detected:
            self._write_drift_event(target, drift_notes)
        return result

    def list_all_targets(self) -> dict:
        return {kind: lane.list_targets() for kind, lane in self.lanes.items()}

    def status_snapshot(self) -> dict:
        snap = {}
        for kind, lane in self.lanes.items():
            targets = lane.list_targets()
            sample = targets[0] if targets else None
            probe = lane.probe(sample) if sample else None
            snap[kind.value] = {
                "tier": lane.tier.value,
                "targets": len(targets),
                "available": probe.available if probe else False,
                "reason": probe.reason if probe else "no targets to probe",
                "probed_target": sample,
                "authenticated": getattr(lane, "is_authenticated", None),
            }
        return snap

    def _check_drift(self, lane: SourceLane, currently_available: bool) -> Optional[str]:
        marker = self.config.drift_log_dir / f"{lane.value}.last_state"
        prev = None
        if marker.exists():
            prev = marker.read_text().strip()
        now = "available" if currently_available else "unavailable"
        marker.write_text(now)
        if prev == "available" and now == "unavailable":
            return f"{lane.value}: was available, now unavailable"
        if prev == "unavailable" and now == "available":
            return f"{lane.value}: recovered"
        return None

    def _write_receipt(self, result: SourceResolutionResult):
        path = self.config.receipts_dir / f"{result.receipt_id}.json"
        path.write_bytes(orjson.dumps(result.model_dump(mode="json"),
                                       option=orjson.OPT_INDENT_2))

    def _write_drift_event(self, target: str, notes: List[str]):
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = self.config.drift_log_dir / f"drift_{ts}.json"
        path.write_bytes(orjson.dumps({
            "ts": datetime.now(timezone.utc).isoformat(),
            "target": target, "notes": notes,
        }, option=orjson.OPT_INDENT_2))


_TIER_RANK = {
    SourceTier.UNVERIFIED: 0,
    SourceTier.MANUAL: 1,
    SourceTier.DERIVED_PUBLIC: 2,
    SourceTier.OFFICIAL_PUBLIC: 3,
    SourceTier.OFFICIAL_AUTHENTICATED: 4,
}

def _tier_ge(a: SourceTier, b: SourceTier) -> bool:
    return _TIER_RANK[a] >= _TIER_RANK[b]
