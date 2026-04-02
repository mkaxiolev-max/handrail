# Copyright © 2026 Axiolev. All rights reserved.
"""
SAN — Sovereign Authority Namespace adapter.
Legal/territorial reality layer. All ops are state-writes + reads.
No external API calls. Stores to /Volumes/NSExternal/ALEXANDRIA/san/
with fallback to ~/.axiolev/san/
"""
from __future__ import annotations
import json, time, uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

_SAN_SSD  = Path("/Volumes/NSExternal/ALEXANDRIA/san")
_SAN_FALL = Path.home() / ".axiolev" / "san"

def _san_root() -> Path:
    if Path("/Volumes/NSExternal/ALEXANDRIA").exists():
        return _SAN_SSD
    return _SAN_FALL

def _san_dir(entity: str) -> Path:
    d = _san_root() / entity
    d.mkdir(parents=True, exist_ok=True)
    return d

def _ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def _write(entity: str, obj_id: str, data: dict) -> None:
    (_san_dir(entity) / f"{obj_id}.json").write_text(json.dumps(data, indent=2))

def _read_all(entity: str) -> list[dict]:
    out = []
    for f in sorted(_san_dir(entity).glob("*.json")):
        try: out.append(json.loads(f.read_text()))
        except Exception: pass
    return out

def _read_one(entity: str, obj_id: str) -> dict | None:
    p = _san_dir(entity) / f"{obj_id}.json"
    if p.exists():
        try: return json.loads(p.read_text())
        except Exception: return None
    return None

def _alexandria_san_log(event: str, data: dict) -> None:
    try:
        log_path = _san_root().parent / "ledger" / "san_events.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a") as f:
            f.write(json.dumps({"event": event, "data": data, "ts": _ts()}) + "\n")
    except Exception: pass

@dataclass
class TerritoryNode:
    id: str; name: str; domain: str; claim_status: str
    owner: str; filed_at: str; expires_at: str; ts: str = ""

@dataclass
class ClaimCoordinate:
    id: str; territory_id: str; concept: str; semantic_anchor: str
    strength: float; coverage: str; ts: str = ""

@dataclass
class WhiteSpaceOpportunity:
    id: str; concept: str; adjacent_claims: list
    openness_score: float; strategic_value: str; ts: str = ""

@dataclass
class RiskZone:
    id: str; territory_id: str; risk_type: str; severity: str
    description: str; mitigation: str; ts: str = ""

@dataclass
class FilingIntent:
    id: str; concept: str; jurisdiction: str; filing_type: str
    target_date: str; status: str; ts: str = ""

@dataclass
class LicensingTarget:
    id: str; territory_id: str; target_entity: str
    license_type: str; value_estimate: str; ts: str = ""

def _op_san_add_territory(args: dict, policy: Any) -> dict:
    obj = TerritoryNode(
        id=args.get("id") or str(uuid.uuid4())[:8],
        name=args.get("name", ""), domain=args.get("domain", ""),
        claim_status=args.get("claim_status", "unclaimed"),
        owner=args.get("owner", "axiolev"),
        filed_at=args.get("filed_at", _ts()), expires_at=args.get("expires_at", ""), ts=_ts(),
    )
    data = asdict(obj); _write("territories", obj.id, data)
    return {"ok": True, "entity": "territory", "id": obj.id, "ts": obj.ts}

def _op_san_map_claim(args: dict, policy: Any) -> dict:
    tid = args.get("territory_id", "")
    if not tid: raise ValueError("san.map_claim requires territory_id")
    obj = ClaimCoordinate(
        id=args.get("id") or str(uuid.uuid4())[:8], territory_id=tid,
        concept=args.get("concept", ""), semantic_anchor=args.get("semantic_anchor", ""),
        strength=float(args.get("strength", 0.5)), coverage=args.get("coverage", "moderate"), ts=_ts(),
    )
    _write("claims", obj.id, asdict(obj))
    return {"ok": True, "entity": "claim", "id": obj.id, "territory_id": tid, "ts": obj.ts}

def _op_san_find_whitespace(args: dict, policy: Any) -> dict:
    territories = _read_all("territories"); claims = _read_all("claims")
    gaps = []
    for domain in {t.get("domain","") for t in territories}:
        dc = [c for c in claims if any(
            t.get("id") == c.get("territory_id") and t.get("domain") == domain
            for t in territories)]
        if len(dc) < 3:
            obj = WhiteSpaceOpportunity(
                id=str(uuid.uuid4())[:8], concept=f"{domain}_expansion",
                adjacent_claims=[c.get("concept","") for c in dc[:3]],
                openness_score=round(1.0 - len(dc)*0.15, 2),
                strategic_value="high" if len(dc) < 2 else "medium", ts=_ts(),
            )
            gaps.append(asdict(obj))
    limit = int(args.get("limit", 5))
    return {"ok": True, "opportunities": gaps[:limit], "total": len(gaps), "ts": _ts()}

def _op_san_flag_risk(args: dict, policy: Any) -> dict:
    obj = RiskZone(
        id=args.get("id") or str(uuid.uuid4())[:8],
        territory_id=args.get("territory_id",""), risk_type=args.get("risk_type","gap"),
        severity=args.get("severity","medium"), description=args.get("description","")[:500],
        mitigation=args.get("mitigation","")[:500], ts=_ts(),
    )
    data = asdict(obj); _write("risks", obj.id, data)
    _alexandria_san_log("RISK_FLAGGED", data)
    return {"ok": True, "entity": "risk", "id": obj.id, "severity": obj.severity, "ts": obj.ts}

def _op_san_file_intent(args: dict, policy: Any) -> dict:
    obj = FilingIntent(
        id=args.get("id") or str(uuid.uuid4())[:8], concept=args.get("concept",""),
        jurisdiction=args.get("jurisdiction","US"), filing_type=args.get("filing_type","patent"),
        target_date=args.get("target_date",""), status=args.get("status","planned"), ts=_ts(),
    )
    _write("filings", obj.id, asdict(obj))
    return {"ok": True, "entity": "filing", "id": obj.id, "status": obj.status, "ts": obj.ts}

def _op_san_add_licensing_target(args: dict, policy: Any) -> dict:
    obj = LicensingTarget(
        id=args.get("id") or str(uuid.uuid4())[:8],
        territory_id=args.get("territory_id",""), target_entity=args.get("target_entity",""),
        license_type=args.get("license_type","non-exclusive"),
        value_estimate=args.get("value_estimate",""), ts=_ts(),
    )
    _write("licensing", obj.id, asdict(obj))
    return {"ok": True, "entity": "licensing_target", "id": obj.id, "ts": obj.ts}

def _op_san_query_territory(args: dict, policy: Any) -> dict:
    tid = args.get("territory_id") or args.get("id","")
    if not tid: raise ValueError("san.query_territory requires territory_id or id")
    node = _read_one("territories", tid)
    if not node: return {"ok": False, "error": f"territory {tid} not found", "ts": _ts()}
    claims = [c for c in _read_all("claims") if c.get("territory_id") == tid]
    risks  = [r for r in _read_all("risks")  if r.get("territory_id") == tid]
    return {"ok": True, "territory": node, "claims": claims, "risks": risks,
            "claim_count": len(claims), "risk_count": len(risks), "ts": _ts()}

def _op_san_sync_with_lexicon(args: dict, policy: Any) -> dict:
    lex_path = _san_root().parent / "lexicon" / "terms.json"
    lexicon_terms: list[str] = []
    if lex_path.exists():
        try: lexicon_terms = json.loads(lex_path.read_text()).get("terms", [])
        except Exception: pass
    claims = _read_all("claims")
    covered = {c.get("concept","").lower() for c in claims}
    gaps = [t for t in lexicon_terms if t.lower() not in covered]
    covered_list = [t for t in lexicon_terms if t.lower() in covered]
    report = {
        "ok": True, "lexicon_terms": len(lexicon_terms),
        "covered_by_san": len(covered_list), "gaps": gaps[:20],
        "gap_count": len(gaps),
        "coverage_pct": round(len(covered_list) / max(len(lexicon_terms),1) * 100, 1),
        "ts": _ts(),
    }
    _write("sync_reports", f"sync_{_ts().replace(':','-')}", report)
    return report

SAN_OPS: dict = {
    "san.add_territory":        _op_san_add_territory,
    "san.map_claim":            _op_san_map_claim,
    "san.find_whitespace":      _op_san_find_whitespace,
    "san.flag_risk":            _op_san_flag_risk,
    "san.file_intent":          _op_san_file_intent,
    "san.add_licensing_target": _op_san_add_licensing_target,
    "san.query_territory":      _op_san_query_territory,
    "san.sync_with_lexicon":    _op_san_sync_with_lexicon,
}
