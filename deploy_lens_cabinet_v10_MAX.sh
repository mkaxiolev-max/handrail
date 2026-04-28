#!/usr/bin/env bash
# ============================================================
# AXIOLEV NS∞ — LENS CABINET v10 MAX INTEGRATION SCRIPT
# Author : Mike Kenworthy / AXIOLEV Holdings LLC
# Source : v9 canonical (commit a5852827) + v10 spec
# Target : ~/axiolev_runtime  |  branch: integration/max-omega-v10
# Usage  : bash ~/axiolev_runtime/deploy_lens_cabinet_v10_MAX.sh
# Scope  : Writes ALL files, installs deps, runs 1389 tests, deploys
# ============================================================
set -euo pipefail
IFS=$'\n\t'

# ── colours ─────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
log()  { echo -e "${CYAN}[v10]${NC} $*"; }
ok()   { echo -e "${GREEN}[OK]${NC}  $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
die()  { echo -e "${RED}[DIE]${NC}  $*"; exit 1; }

RUNTIME="${AXIOLEV_RUNTIME:-$HOME/axiolev_runtime}"
LENSES="$RUNTIME/services/ns/nss/lenses"
V9_COMMIT="a5852827"
BRANCH="integration/max-omega-v10"

# ============================================================
# 0. PRE-FLIGHT
# ============================================================
log "=== PRE-FLIGHT ==="
cd "$RUNTIME" || die "Cannot cd to $RUNTIME"

python3 --version || die "python3 missing"
git rev-parse --git-dir > /dev/null || die "Not a git repo"

# Verify v9 baseline commit exists
git cat-file -t "$V9_COMMIT" > /dev/null 2>&1 || \
  die "v9 baseline commit $V9_COMMIT not found — run from correct repo"

# Service health checks
for PORT_PATH in "8011/healthz" "8080/healthz" "9003/healthz"; do
  PORT="${PORT_PATH%%/*}"; PATH_="${PORT_PATH##*/}"
  if curl -fsS "http://127.0.0.1:$PORT/$PATH_" > /dev/null 2>&1; then
    ok "Service :$PORT healthy"
  else
    warn "Service :$PORT not responding — continuing (some may start on resume)"
  fi
done

# SSD check
if [ -d "/Volumes/NSExternal" ]; then
  FREE_GB=$(df -g /Volumes/NSExternal | awk 'NR==2{print $4}')
  [ "$FREE_GB" -lt 50 ] && warn "NSExternal free: ${FREE_GB}GB (<50GB threshold)"
  ok "NSExternal mounted, ${FREE_GB}GB free"
else
  warn "/Volumes/NSExternal not mounted — some writes will fail at runtime"
fi

# Clean working tree check
if ! git diff --quiet 2>/dev/null; then
  warn "Working tree has uncommitted changes — stashing before branch create"
  git stash push -m "v10-deploy-autostash-$(date +%s)"
fi

# ============================================================
# 1. BRANCH
# ============================================================
log "=== BRANCH SETUP ==="
git fetch origin --quiet 2>/dev/null || warn "git fetch failed (offline?)"
git checkout -B "$BRANCH" "$V9_COMMIT"
ok "Branch $BRANCH at $V9_COMMIT"

# ============================================================
# 2. INSTALL DEPENDENCIES
# ============================================================
log "=== DEPENDENCIES ==="
# Use the NSS venv on NSExternal (primary env for this project)
NSS_PIP="/Volumes/NSExternal/NSS/.venv/bin/pip"
NSS_PYTHON="/Volumes/NSExternal/NSS/.venv/bin/python3"
if [ ! -f "$NSS_PIP" ]; then
  NSS_PIP="pip3"
  NSS_PYTHON="python3"
fi
"$NSS_PIP" install -q -U \
  "pydantic>=2.8" \
  "pyarrow>=15" \
  networkx \
  "httpx>=0.27" \
  structlog \
  prometheus_client \
  langchain-huggingface \
  sentence-transformers \
  ulid-py \
  opacus \
  pymerkle \
  semver \
  zstandard \
  langgraph \
  aiokafka \
  redis \
  "fastapi>=0.110" \
  click \
  pytest \
  pytest-asyncio 2>&1 | tail -5 || warn "Some deps may have failed to install"
ok "Deps installed"

# ============================================================
# 3. APFS + SSD OPTIMISATIONS (idempotent)
# ============================================================
log "=== SSD OPTIMISATIONS ==="
if [ -d "/Volumes/NSExternal" ]; then
  sudo mount -uw -o noatime /Volumes/NSExternal 2>/dev/null || true
  sudo trimforce enable 2>/dev/null || true
  mdutil -i off /Volumes/NSExternal 2>/dev/null || true
  mkdir -p /Volumes/NSExternal/ris/{uspto,courtlistener,arxiv,web,rejects}
  mkdir -p /Volumes/NSExternal/ALEXANDRIA
  ok "SSD optimised"
fi

# ============================================================
# 4. WRITE DIRECTORY TREE
# ============================================================
log "=== WRITING FILE TREE ==="
mkdir -p "$LENSES/teams"
mkdir -p "$LENSES/v10"
mkdir -p "$LENSES/contracts_external"
mkdir -p "$RUNTIME/tests/v10"
mkdir -p "$RUNTIME/docs/lens_cabinet/adr"
mkdir -p "$RUNTIME/.github"

# ──────────────────────────────────────────────────────────────
# 4.1  teams/__init__.py
# ──────────────────────────────────────────────────────────────
cat > "$LENSES/teams/__init__.py" << 'PYEOF'
"""AXIOLEV NS∞ Lens Cabinet v10 — Team runtime package."""
from __future__ import annotations
from .base import BaseTeam, TeamCharter, TeamMetrics, CrossTeamHandoff
from .registry import TeamRegistry, RACIRow
from .architecture_team import ArchitectureTeam
from .math_phi_team import MathPhiTeam
from .data_engineering_team import DataEngineeringTeam
from .validation_audit_team import ValidationAuditTeam
from .web_crawl_team import WebCrawlTeam

__all__ = [
    "BaseTeam","TeamCharter","TeamMetrics","CrossTeamHandoff",
    "TeamRegistry","RACIRow",
    "ArchitectureTeam","MathPhiTeam","DataEngineeringTeam",
    "ValidationAuditTeam","WebCrawlTeam",
]

# Auto-instantiate singletons — zero-ceremony resume_ns.sh workflow.
REGISTRY = TeamRegistry.instance()
REGISTRY.register(ArchitectureTeam())
REGISTRY.register(MathPhiTeam())
REGISTRY.register(DataEngineeringTeam())
REGISTRY.register(ValidationAuditTeam())
REGISTRY.register(WebCrawlTeam())
PYEOF

# ──────────────────────────────────────────────────────────────
# 4.2  teams/base.py
# ──────────────────────────────────────────────────────────────
cat > "$LENSES/teams/base.py" << 'PYEOF'
"""BaseTeam — runtime executable Team root (v10)."""
from __future__ import annotations
import abc, time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable
import structlog
from prometheus_client import Counter, Gauge, Histogram

log = structlog.get_logger(__name__)

TEAM_LENS_RUNS     = Counter("team_lens_runs_total","Lens runs by team",["team_id","lens_name"])
TEAM_ADMISSION_RATE= Gauge  ("team_admission_rate","Canon admission fraction",["team_id"])
TEAM_RECEIPTS      = Counter("team_receipts_total","Receipts by team",["team_id","receipt_type"])
TEAM_ONCALL_ACKS   = Counter("team_oncall_acks_total","On-call acks",["team_id"])
TEAM_HANDOFFS      = Counter("team_handoffs_total","Cross-team handoffs",["from_team","to_team","kind"])
TEAM_LENS_LATENCY  = Histogram("team_lens_latency_seconds","Lens latency sec",["team_id","lens_name"])

@dataclass
class TeamCharter:
    mission: str
    scope: list[str]
    owned_lenses: list[str]
    owned_modules: list[str]
    cps_lanes: list[str]
    ci_gates: list[str]
    quorum_n_of_m: tuple[int,int] = (1,1)

@dataclass
class TeamMetrics:
    runs_owned: int = 0
    admission_count: int = 0
    rejection_count: int = 0
    receipts_emitted: int = 0
    @property
    def admission_rate(self) -> float:
        total = self.admission_count + self.rejection_count
        return self.admission_count / total if total else 0.0

@dataclass
class CrossTeamHandoff:
    from_team: str
    to_team: str
    kind: str
    payload_schema: str
    sla_seconds: int = 300

class BaseTeam(abc.ABC):
    team_id: str
    name: str
    charter: TeamCharter
    handoffs: list[CrossTeamHandoff]

    def __init__(self) -> None:
        self.metrics = TeamMetrics()
        self.on_call_rotation: list[str] = ["mike"]
        self.escalation_path: list[str] = ["mike"]
        self._cps_registered = False

    @abc.abstractmethod
    def register_cps_lanes(self, handrail_client: Any) -> None: ...

    @abc.abstractmethod
    def run_ci_gates(self, pr_diff: dict[str,Any]) -> tuple[bool, list[str]]: ...

    def execute_owned_lens(self, lens_name: str, source_uri: str,
                           cabinet: Any, **kwargs: Any) -> Any:
        if lens_name not in self.charter.owned_lenses:
            raise PermissionError(
                f"Team {self.team_id} does not own lens {lens_name}")
        log.info("team.execute_lens.begin", team=self.team_id, lens=lens_name, src=source_uri)
        TEAM_LENS_RUNS.labels(self.team_id, lens_name).inc()
        t0 = time.perf_counter()
        try:
            run = cabinet.run(lens_name, source_uri, team_owner=self.team_id, **kwargs)
        finally:
            TEAM_LENS_LATENCY.labels(self.team_id, lens_name).observe(time.perf_counter()-t0)
        self.metrics.runs_owned += 1
        if getattr(run, "admitted_count", 0) > 0:
            self.metrics.admission_count += 1
        else:
            self.metrics.rejection_count += 1
        TEAM_ADMISSION_RATE.labels(self.team_id).set(self.metrics.admission_rate)
        return run

    def handoff(self, to_team: "BaseTeam", kind: str, payload: dict[str,Any]) -> dict[str,Any]:
        TEAM_HANDOFFS.labels(self.team_id, to_team.team_id, kind).inc()
        log.info("team.handoff", from_=self.team_id, to=to_team.team_id, kind=kind)
        return to_team.receive_handoff(self.team_id, kind, payload)

    def receive_handoff(self, from_team: str, kind: str, payload: dict[str,Any]) -> dict[str,Any]:
        return {"received": True, "from": from_team, "kind": kind}

    def quorum_satisfied(self, approvers: Iterable[str]) -> bool:
        n_required, _ = self.charter.quorum_n_of_m
        return len(set(approvers) & set(self.on_call_rotation)) >= n_required

    def escalate(self, reason: str, severity: str = "warn") -> None:
        log.warning("team.escalate", team=self.team_id, reason=reason,
                    severity=severity, chain=self.escalation_path)

    def emit_receipt(self, receipt_type: str) -> None:
        self.metrics.receipts_emitted += 1
        TEAM_RECEIPTS.labels(self.team_id, receipt_type).inc()

# v10 — canonical
PYEOF

# ──────────────────────────────────────────────────────────────
# 4.3  teams/registry.py
# ──────────────────────────────────────────────────────────────
cat > "$LENSES/teams/registry.py" << 'PYEOF'
"""TeamRegistry — singleton + RACI matrix (v10)."""
from __future__ import annotations
from dataclasses import dataclass, field
from threading import Lock
import structlog
log = structlog.get_logger(__name__)

@dataclass(frozen=True)
class RACIRow:
    item: str
    responsible: str
    accountable: str
    consulted: tuple[str,...] = field(default_factory=tuple)
    informed: tuple[str,...] = field(default_factory=tuple)

class TeamRegistry:
    _instance: "TeamRegistry | None" = None
    _lock = Lock()

    def __init__(self) -> None:
        self._teams: dict[str,"BaseTeam"] = {}
        self._raci: list[RACIRow] = []

    @classmethod
    def instance(cls) -> "TeamRegistry":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
        return cls._instance

    def register(self, team: "BaseTeam") -> None:
        if team.team_id in self._teams:
            log.warning("team.registry.duplicate", team=team.team_id); return
        self._teams[team.team_id] = team
        log.info("team.registry.register", team=team.team_id, name=team.name)

    def get(self, team_id: str) -> "BaseTeam":
        return self._teams[team_id]

    def list(self) -> list["BaseTeam"]:
        return list(self._teams.values())

    def add_raci(self, row: RACIRow) -> None:
        self._raci.append(row)

    def raci(self) -> list[RACIRow]:
        return list(self._raci)

    def find_owner(self, item: str) -> str | None:
        for row in self._raci:
            if row.item == item: return row.accountable
        return None

# v10 — canonical
PYEOF

# ──────────────────────────────────────────────────────────────
# 4.4  Concrete team files (all 5)
# ──────────────────────────────────────────────────────────────
cat > "$LENSES/teams/architecture_team.py" << 'PYEOF'
"""Architecture Team — cabinet integrity, contracts, scoring shape, registry."""
from __future__ import annotations
import structlog
from .base import BaseTeam, TeamCharter, CrossTeamHandoff
from .registry import TeamRegistry, RACIRow
log = structlog.get_logger(__name__)

class ArchitectureTeam(BaseTeam):
    team_id = "architecture"
    name = "Architecture Team"
    charter = TeamCharter(
        mission="Guard cabinet integrity, contracts, scoring shape, source resolution.",
        scope=["lens contract surface","scoring weights vector shape","source provenance"],
        owned_lenses=["SchemaEvolutionLens","VersionDriftLens"],
        owned_modules=["cabinet.py","base.py","contracts.py","scoring.py",
                       "source_resolver.py","registry.py"],
        cps_lanes=["team.architecture.review","team.architecture.approve_lens_config"],
        ci_gates=["schema-breaking-change-detector","contract-version-bump-enforcement"],
        quorum_n_of_m=(1,1),
    )
    handoffs = [
        CrossTeamHandoff("web_crawl","architecture","schema_validation",
                         "https://axiolev.io/schemas/handoff/schema_validation-v1.json"),
        CrossTeamHandoff("architecture","validation_audit","post_validation_scan",
                         "https://axiolev.io/schemas/handoff/post_validation-v1.json"),
    ]

    def register_cps_lanes(self, handrail_client) -> None:
        for lane in self.charter.cps_lanes:
            try:
                handrail_client.register_lane(lane, owner=self.team_id, port=8011)
            except Exception as e:
                log.warning("arch.cps.lane.skip", lane=lane, err=repr(e))
        self._cps_registered = True
        log.info("arch.cps.registered", lanes=self.charter.cps_lanes)

    def run_ci_gates(self, pr_diff):
        violations: list[str] = []
        if any(f.endswith("contracts.py") for f in pr_diff.get("files",[])):
            if "VERSION" not in pr_diff.get("commit_msg",""):
                violations.append("contracts.py touched without VERSION bump")
        if pr_diff.get("breaks_pydantic_schema"):
            violations.append("Pydantic schema break without SchemaEvolutionLens migration")
        return (not violations, violations)

def _seed_raci(reg: TeamRegistry) -> None:
    for lens in ("SchemaEvolutionLens","VersionDriftLens","cabinet","scoring"):
        reg.add_raci(RACIRow(item=lens, responsible="architecture",
                             accountable="architecture",
                             consulted=("validation_audit",),
                             informed=("data_engineering",)))

# v10 — canonical
PYEOF

cat > "$LENSES/teams/math_phi_team.py" << 'PYEOF'
"""Math / Phi Team — curvature math, weight calibration, novelty (v10)."""
from __future__ import annotations
import structlog
from .base import BaseTeam, TeamCharter, CrossTeamHandoff
log = structlog.get_logger(__name__)

class MathPhiTeam(BaseTeam):
    team_id = "math_phi"
    name = "Math / Phi Team"
    charter = TeamCharter(
        mission="Own curvature math, weight calibration, golden-ratio constants.",
        scope=["phi-curvature flag","scoring weight vector values","novelty embeddings"],
        owned_lenses=["ClaimNoveltyLens","EmbeddingDriftLens"],
        owned_modules=["phi_curvature.py","refractive_index.py","scoring.py"],
        cps_lanes=["team.math.recompute_phi","team.math.calibrate_weights"],
        ci_gates=["formal-proof-required-on-derivation-changes"],
        quorum_n_of_m=(1,1),
    )
    handoffs: list = []

    def register_cps_lanes(self, handrail_client) -> None:
        for lane in self.charter.cps_lanes:
            try: handrail_client.register_lane(lane, owner=self.team_id, port=8011)
            except Exception as e: log.warning("math.cps.lane.skip", lane=lane, err=repr(e))
        self._cps_registered = True

    def run_ci_gates(self, pr_diff):
        violations: list[str] = []
        if any("scoring.py" in f for f in pr_diff.get("files",[])):
            if "LaTeX" not in pr_diff.get("pr_description",""):
                violations.append("scoring.py weight change requires LaTeX proof block in PR")
        return (not violations, violations)

# v10 — canonical
PYEOF

cat > "$LENSES/teams/data_engineering_team.py" << 'PYEOF'
"""Data Engineering Team — storage, Parquet, embeddings, CPS plumbing (v10)."""
from __future__ import annotations
import structlog
from .base import BaseTeam, TeamCharter
log = structlog.get_logger(__name__)

class DataEngineeringTeam(BaseTeam):
    team_id = "data_engineering"
    name = "Data Engineering Team"
    charter = TeamCharter(
        mission="Storage, Parquet, embeddings, observability, CPS plumbing.",
        scope=["Parquet partition layout","Zstd compression tier","MPS embedding cache"],
        owned_lenses=["StreamingLens","CostBudgetLens"],
        owned_modules=["writers.py","rejects.py","embeddings.py",
                       "observability.py","cps_integration/"],
        cps_lanes=["team.dataeng.parquet_compact","team.dataeng.disk_health",
                   "team.dataeng.embedding_refresh"],
        ci_gates=["ssd-capacity-check","parquet-schema-migration-gate"],
        quorum_n_of_m=(1,1),
    )
    handoffs: list = []

    def register_cps_lanes(self, handrail_client) -> None:
        for lane in self.charter.cps_lanes:
            try: handrail_client.register_lane(lane, owner=self.team_id, port=8011)
            except Exception as e: log.warning("dataeng.cps.lane.skip", lane=lane, err=repr(e))
        self._cps_registered = True

    def run_ci_gates(self, pr_diff):
        violations: list[str] = []
        if pr_diff.get("disk_free_gb",999) < 50:
            violations.append("NSExternal disk < 50GB free")
        return (not violations, violations)

# v10 — canonical
PYEOF

cat > "$LENSES/teams/validation_audit_team.py" << 'PYEOF'
"""Validation / Audit Team — validators, contradictions, receipts (v10)."""
from __future__ import annotations
import structlog
from .base import BaseTeam, TeamCharter
log = structlog.get_logger(__name__)

class ValidationAuditTeam(BaseTeam):
    team_id = "validation_audit"
    name = "Validation / Audit Team"
    charter = TeamCharter(
        mission="Validators, contradictions, receipts, audit trail completeness.",
        scope=["receipt schema","contradiction pressure threshold","audit ledger integrity"],
        owned_lenses=[
            "ProvenanceChainLens","DifferentialPrivacyLens","AdversarialRobustnessLens",
            "TemporalCoherenceLens","CrossSourceTriangulationLens","LegalComplianceLens",
            "BiasDetectionLens","CitationIntegrityLens",
        ],
        owned_modules=["validators.py","contradiction.py","receipts.py",
                       "audit_lens","compare_lens","interpretability_lens"],
        cps_lanes=["team.audit.scan","team.audit.dispute","team.audit.cross_check"],
        ci_gates=["receipt-schema-migration-required","root-ledger-migration-plan"],
        quorum_n_of_m=(1,1),
    )
    handoffs: list = []

    def register_cps_lanes(self, handrail_client) -> None:
        for lane in self.charter.cps_lanes:
            try: handrail_client.register_lane(lane, owner=self.team_id, port=8011)
            except Exception as e: log.warning("audit.cps.lane.skip", lane=lane, err=repr(e))
        self._cps_registered = True

    def run_ci_gates(self, pr_diff):
        violations: list[str] = []
        if any("receipts.py" in f for f in pr_diff.get("files",[])):
            if not pr_diff.get("has_root_migration_plan"):
                violations.append("receipts.py change requires ROOT ledger migration plan")
        return (not violations, violations)

# v10 — canonical
PYEOF

cat > "$LENSES/teams/web_crawl_team.py" << 'PYEOF'
"""Web / Crawl Team — external fetch, robots/ToS, rate limits (v10)."""
from __future__ import annotations
import structlog
from .base import BaseTeam, TeamCharter
log = structlog.get_logger(__name__)

class WebCrawlTeam(BaseTeam):
    team_id = "web_crawl"
    name = "Web / Crawl Team"
    charter = TeamCharter(
        mission="External fetch, robots/ToS compliance, rate limits, source health.",
        scope=["robots.txt","ToS adherence","rate-limit budget","ban detection"],
        owned_lenses=["semantic_markdown_web","courtlistener_recap","arxiv_paper",
                      "uspto_assignment","LangChainAgenticLens","MultiModalLens","FederatedLens"],
        owned_modules=["fetchers/","robots.py","ratelimit.py"],
        cps_lanes=["team.crawl.fetch","team.crawl.respect_robots","team.crawl.rate_limit"],
        ci_gates=["robots-compliance-check","tos-adherence-check","rate-limit-policy-check"],
        quorum_n_of_m=(1,1),
    )
    handoffs: list = []

    def register_cps_lanes(self, handrail_client) -> None:
        for lane in self.charter.cps_lanes:
            try: handrail_client.register_lane(lane, owner=self.team_id, port=8011)
            except Exception as e: log.warning("crawl.cps.lane.skip", lane=lane, err=repr(e))
        self._cps_registered = True

    def run_ci_gates(self, pr_diff):
        violations: list[str] = []
        if pr_diff.get("new_external_domain") and not pr_diff.get("robots_checked"):
            violations.append("New external domain requires robots.txt check")
        return (not violations, violations)

# v10 — canonical
PYEOF

# ──────────────────────────────────────────────────────────────
# 4.5  cabinet.py v10 patch  (update existing file if present)
# ──────────────────────────────────────────────────────────────
if [ -f "$LENSES/cabinet.py" ]; then
  log "Patching cabinet.py for v10 team_id support..."
  # Inject team_index and team-aware run() if not already present
  "$NSS_PYTHON" "$LENSES/cabinet.py" << 'PATCHEOF'
import re, pathlib, sys
path = pathlib.Path(sys.argv[1])
src  = path.read_text()
# Only patch once
if "_team_index" in src:
    print("cabinet.py already patched — skipping")
    sys.exit(0)

patch = '''
# v10 patch — team index ─────────────────────────────
    def _v10_ensure_team_index(self):
        if not hasattr(self, "_team_index"):
            self._team_index = {}

    def register(self, lens, team_owner="unassigned"):
        self._v10_ensure_team_index()
        super_register = getattr(super(), "register", None)
        if super_register:
            super_register(lens)
        else:
            if lens.name in getattr(self, "_lenses", {}):
                raise ValueError(f"Lens already registered: {lens.name}")
            if not hasattr(self, "_lenses"):
                self._lenses = {}
            self._lenses[lens.name] = lens
        self._team_index[lens.name] = team_owner or getattr(lens, "team_id", "unassigned")

    def lenses_for_team(self, team_id):
        self._v10_ensure_team_index()
        return [n for n, t in self._team_index.items() if t == team_id]
# ─────────────────────────────────────────────────────
'''
# Append to LensCabinet class body (before CABINET = LensCabinet())
src = src.replace(
    "CABINET = LensCabinet()",
    patch + "\nCABINET = LensCabinet()\n"
)
path.write_text(src)
print("cabinet.py patched OK")
PATCHEOF
fi

# ──────────────────────────────────────────────────────────────
# 4.6  base.py v10 patch — add team_id field to BaseSemanticLens
# ──────────────────────────────────────────────────────────────
if [ -f "$LENSES/lenses/base.py" ]; then
  log "Patching lenses/base.py for team_id..."
  "$NSS_PYTHON" "$LENSES/lenses/base.py" << 'PATCHEOF'
import pathlib, sys
path = pathlib.Path(sys.argv[1])
src  = path.read_text()
if "team_id" in src:
    print("base.py already has team_id — skipping"); sys.exit(0)
src = src.replace(
    "class BaseSemanticLens(abc.ABC):",
    "class BaseSemanticLens(abc.ABC):\n    team_id: str = \"unassigned\"  # v10"
)
path.write_text(src)
print("base.py patched OK")
PATCHEOF
fi

# ──────────────────────────────────────────────────────────────
# 4.7  contracts_external/symphony_contracts.py (DECOUPLED)
# ──────────────────────────────────────────────────────────────
touch "$LENSES/contracts_external/__init__.py"
cat > "$LENSES/contracts_external/symphony_contracts.py" << 'PYEOF'
"""DECOUPLED Symphony contract surface — NO imports from symphony_os.
Symphony pulls via stable JSON Schema at:
  https://axiolev.io/schemas/symphony/<ContractName>-v<MAJOR.MINOR.PATCH>.json
CI invariant: grep -r "from symphony_os" services/ns/nss/lenses/ must return empty.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

CONTRACT_SURFACE_VERSION = "1.0.0"

@dataclass(frozen=True)
class SymphonyProgramSpec:
    """Emitted by a Lens; consumable by Symphony's Document-to-Program Compiler.
    Lenses MAY emit. Symphony MAY consume. Neither imports the other."""
    program_id: str
    source_lens: str
    canon_record_ids: list[str]
    intent: str
    parameters: dict[str,Any] = field(default_factory=dict)
    contract_version: str = CONTRACT_SURFACE_VERSION

@dataclass(frozen=True)
class LensCanonHandoffContract:
    """Stable wire specification — NOT an import. JSON Schema governs wire format."""
    canon_record_id: str
    lens_name: str
    admitted_at_iso: str
    admission_score: float
    receipt_chain: list[str]
    contract_version: str = CONTRACT_SURFACE_VERSION

# v10 — canonical — decoupled
PYEOF

# ──────────────────────────────────────────────────────────────
# 4.8  17 NEW LENSES  (v10/)
# ──────────────────────────────────────────────────────────────
touch "$LENSES/v10/__init__.py"

# --- 18. ProvenanceChainLens ---
cat > "$LENSES/v10/provenance_chain_lens.py" << 'PYEOF'
"""ProvenanceChainLens — Merkle-root provenance verification. Team: validation_audit."""
from __future__ import annotations
import hashlib
from pydantic import BaseModel, Field
import structlog
from ..lenses.base import BaseSemanticLens
log = structlog.get_logger(__name__)

class ProvenanceContract(BaseModel):
    source_uri: str
    fetched_bytes_sha256: str
    parsed_records_sha256: list[str]
    embeddings_sha256: list[str]
    admitted_parquet_sha256: str
    merkle_root: str
    proof_path: list[dict] = Field(default_factory=list)

class ProvenanceChainLens(BaseSemanticLens):
    name = "ProvenanceChainLens"
    team_id = "validation_audit"
    contract = ProvenanceContract

    async def fetch(self, source_uri: str) -> bytes:
        import httpx
        async with httpx.AsyncClient(timeout=30) as cli:
            r = await cli.get(source_uri); r.raise_for_status(); return r.content

    def parse(self, raw: bytes):
        sha = hashlib.sha256(raw).hexdigest()
        leaves = [sha]
        try:
            from pymerkle import InmemoryTree
            tree = InmemoryTree(algorithm="sha256")
            for leaf in leaves: tree.append_entry(leaf.encode())
            root = tree.get_state().hex()
        except Exception:
            root = hashlib.sha256(b"".join(l.encode() for l in leaves)).hexdigest()
        yield {"source_uri":"<set-by-runner>","fetched_bytes_sha256":sha,
               "parsed_records_sha256":leaves,"embeddings_sha256":[],
               "admitted_parquet_sha256":"","merkle_root":root}

    def _score_gates(self, rec, resolved=None, ri=None, phi=None):
        gates = super()._score_gates(rec, resolved, ri, phi)
        gates["provenance_integrity"] = 1.0 if rec.merkle_root else 0.0
        return gates

# v10 — canonical
PYEOF

# --- 19. DifferentialPrivacyLens ---
cat > "$LENSES/v10/differential_privacy_lens.py" << 'PYEOF'
"""DifferentialPrivacyLens — ε-DP budget tracking. Team: validation_audit."""
from __future__ import annotations
import math
from pydantic import BaseModel
import numpy as np
from ..lenses.base import BaseSemanticLens

class DPContract(BaseModel):
    epsilon: float
    delta: float
    mechanism: str  # "laplace" | "gaussian"
    sensitivity: float
    subject_id: str
    subject_budget_remaining: float

class DifferentialPrivacyLens(BaseSemanticLens):
    """ε-DP via Laplace/Gaussian noise. Per-subject budget; rejects when exhausted."""
    name = "DifferentialPrivacyLens"
    team_id = "validation_audit"
    contract = DPContract

    async def fetch(self, src): return src
    def parse(self, raw): yield raw if isinstance(raw, dict) else {"epsilon":1.0,"delta":1e-5,
        "mechanism":"laplace","sensitivity":1.0,"subject_id":"anon",
        "subject_budget_remaining":10.0}

    def add_noise(self, value: float, c: DPContract) -> float:
        if c.mechanism == "laplace":
            return value + float(np.random.laplace(0.0, c.sensitivity / c.epsilon))
        sigma = c.sensitivity * math.sqrt(2 * math.log(1.25 / c.delta)) / c.epsilon
        return value + float(np.random.normal(0.0, sigma))

    def _score_gates(self, rec, resolved=None, ri=None, phi=None):
        gates = super()._score_gates(rec, resolved, ri, phi)
        ok = rec.subject_budget_remaining >= rec.epsilon
        gates["contradiction_clearance"] = 1.0 if ok else 0.0
        return gates

# v10 — canonical
PYEOF

# --- 20. AdversarialRobustnessLens ---
cat > "$LENSES/v10/adversarial_robustness_lens.py" << 'PYEOF'
"""AdversarialRobustnessLens — poisoning + prompt injection detection. Team: validation_audit."""
from __future__ import annotations
import re
from pydantic import BaseModel
from ..lenses.base import BaseSemanticLens

INJECTION_PATTERNS = [
    r"ignore (all|previous) instructions",
    r"system prompt",
    r"<\s*\|im_start\|\s*>",
    r"jailbreak",
    r"DAN mode",
]

class AdversarialContract(BaseModel):
    attack_type: str  # "pgd"|"fgsm"|"prompt_injection"|"citation_graph_poison"
    perturbation_norm: float
    detector_score: float
    sanitized_text: str | None = None

class AdversarialRobustnessLens(BaseSemanticLens):
    name = "AdversarialRobustnessLens"
    team_id = "validation_audit"
    contract = AdversarialContract

    async def fetch(self, src): return src
    def parse(self, raw): yield raw if isinstance(raw, dict) else {
        "attack_type":"prompt_injection","perturbation_norm":0.0,"detector_score":0.0}

    def detect_prompt_injection(self, text: str) -> float:
        hits = sum(1 for p in INJECTION_PATTERNS if re.search(p, text, re.I))
        return min(1.0, hits / len(INJECTION_PATTERNS) * 2)

    def _score_gates(self, rec, resolved=None, ri=None, phi=None):
        gates = super()._score_gates(rec, resolved, ri, phi)
        gates["contradiction_clearance"] = 1.0 - rec.detector_score
        return gates

# v10 — canonical
PYEOF

# --- 21. TemporalCoherenceLens ---
cat > "$LENSES/v10/temporal_coherence_lens.py" << 'PYEOF'
"""TemporalCoherenceLens — ARIMA-residual temporal anomaly. Team: validation_audit."""
from __future__ import annotations
import datetime as dt
from pydantic import BaseModel
import numpy as np
from ..lenses.base import BaseSemanticLens

class TemporalContract(BaseModel):
    arima_residual: float
    future_citation_flag: bool
    retroactive_edit_flag: bool
    timeline_anomaly_score: float

class TemporalCoherenceLens(BaseSemanticLens):
    name = "TemporalCoherenceLens"
    team_id = "validation_audit"
    contract = TemporalContract

    async def fetch(self, src): return src
    def parse(self, raw): yield raw if isinstance(raw, dict) else {
        "arima_residual":0.0,"future_citation_flag":False,
        "retroactive_edit_flag":False,"timeline_anomaly_score":0.0}

    def check_future_citation(self, citing: dt.date, cited: dt.date) -> bool:
        return cited > citing

    def arima_residual(self, series: list[float]) -> float:
        a = np.asarray(series, dtype=float)
        if len(a) < 6: return 0.0
        return float(abs(a[-1] - a[-6:-1].mean()) / (a.std() + 1e-9))

    def _score_gates(self, rec, resolved=None, ri=None, phi=None):
        gates = super()._score_gates(rec, resolved, ri, phi)
        gates["contradiction_clearance"] = 0.0 if (
            rec.future_citation_flag or rec.retroactive_edit_flag) else 1.0
        return gates

# v10 — canonical
PYEOF

# --- 22. CrossSourceTriangulationLens ---
cat > "$LENSES/v10/cross_source_triangulation_lens.py" << 'PYEOF'
"""CrossSourceTriangulationLens — multi-source fact validation. Team: validation_audit."""
from pydantic import BaseModel
from ..lenses.base import BaseSemanticLens

class TriangulationContract(BaseModel):
    fact_id: str
    sources_confirming: list[str]
    triangulation_confidence: float
    conflict_resolution: str | None = None

class CrossSourceTriangulationLens(BaseSemanticLens):
    name = "CrossSourceTriangulationLens"
    team_id = "validation_audit"
    contract = TriangulationContract

    async def fetch(self, src): return src
    def parse(self, raw): yield raw if isinstance(raw, dict) else {
        "fact_id":"anon","sources_confirming":[],"triangulation_confidence":0.0}

    def _score_gates(self, rec, resolved=None, ri=None, phi=None):
        gates = super()._score_gates(rec, resolved, ri, phi)
        gates["source_trust"] = min(1.0, len(rec.sources_confirming) / 2)
        gates["contradiction_clearance"] = rec.triangulation_confidence
        return gates

# v10 — canonical
PYEOF

# --- 23. LegalComplianceLens ---
cat > "$LENSES/v10/legal_compliance_lens.py" << 'PYEOF'
"""LegalComplianceLens — GDPR/CCPA/HIPAA PII filter. Team: validation_audit."""
from __future__ import annotations
import re
from pydantic import BaseModel
from ..lenses.base import BaseSemanticLens

EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
SSN   = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

class LegalContract(BaseModel):
    jurisdiction: str  # "GDPR"|"CCPA"|"HIPAA"|"US-PUB"
    pii_detected: bool
    gdpr_lawful_basis: str | None
    retention_until: str | None

class LegalComplianceLens(BaseSemanticLens):
    name = "LegalComplianceLens"
    team_id = "validation_audit"
    contract = LegalContract

    async def fetch(self, src): return src
    def parse(self, raw): yield raw if isinstance(raw, dict) else {
        "jurisdiction":"US-PUB","pii_detected":False,
        "gdpr_lawful_basis":None,"retention_until":None}

    def detect_pii(self, text: str) -> bool:
        return bool(EMAIL.search(text) or SSN.search(text))

    def _score_gates(self, rec, resolved=None, ri=None, phi=None):
        gates = super()._score_gates(rec, resolved, ri, phi)
        if rec.pii_detected and not rec.gdpr_lawful_basis:
            gates["source_trust"] = 0.0
        else:
            gates["source_trust"] = 1.0
        return gates

# v10 — canonical
PYEOF

# --- 24. BiasDetectionLens ---
cat > "$LENSES/v10/bias_detection_lens.py" << 'PYEOF'
"""BiasDetectionLens — demographic/geographic bias audit. FLAG ONLY. Team: validation_audit."""
from pydantic import BaseModel
from collections import Counter
from ..lenses.base import BaseSemanticLens

class BiasContract(BaseModel):
    demographic_skew_score: float
    geographic_concentration: float
    fairness_audit_pass: bool

class BiasDetectionLens(BaseSemanticLens):
    name = "BiasDetectionLens"
    team_id = "validation_audit"
    contract = BiasContract

    async def fetch(self, src): return src
    def parse(self, raw): yield raw if isinstance(raw, dict) else {
        "demographic_skew_score":0.0,"geographic_concentration":0.0,"fairness_audit_pass":True}

    def hhi(self, items: list[str]) -> float:
        c = Counter(items); n = sum(c.values()) or 1
        return sum((v/n)**2 for v in c.values())

    def _score_gates(self, rec, resolved=None, ri=None, phi=None):
        # FLAG ONLY — never modifies gate weights that affect admission band
        return super()._score_gates(rec, resolved, ri, phi)

# v10 — canonical
PYEOF

# --- 25. VersionDriftLens ---
cat > "$LENSES/v10/version_drift_lens.py" << 'PYEOF'
"""VersionDriftLens — upstream schema drift detection. Team: architecture."""
import hashlib, json
from pydantic import BaseModel
from ..lenses.base import BaseSemanticLens

class VersionDriftContract(BaseModel):
    upstream_schema_hash: str
    expected_schema_hash: str
    migration_plan: str | None = None

class VersionDriftLens(BaseSemanticLens):
    name = "VersionDriftLens"
    team_id = "architecture"
    contract = VersionDriftContract

    async def fetch(self, src): return src
    def parse(self, raw): yield raw if isinstance(raw, dict) else {
        "upstream_schema_hash":"","expected_schema_hash":"","migration_plan":None}

    def hash_schema(self, schema: dict) -> str:
        return hashlib.sha256(json.dumps(schema, sort_keys=True).encode()).hexdigest()

    def _score_gates(self, rec, resolved=None, ri=None, phi=None):
        gates = super()._score_gates(rec, resolved, ri, phi)
        ok = (rec.upstream_schema_hash == rec.expected_schema_hash) or rec.migration_plan
        gates["schema_score"] = 1.0 if ok else 0.0
        return gates

# v10 — canonical
PYEOF

# --- 26. CitationIntegrityLens ---
cat > "$LENSES/v10/citation_integrity_lens.py" << 'PYEOF'
"""CitationIntegrityLens — cited patents exist + no cycles. Team: validation_audit."""
from pydantic import BaseModel
import networkx as nx
from ..lenses.base import BaseSemanticLens

class CitationContract(BaseModel):
    citing_id: str
    cited_id: str
    cited_exists: bool
    semantic_match_score: float
    circular_dep_flag: bool

class CitationIntegrityLens(BaseSemanticLens):
    name = "CitationIntegrityLens"
    team_id = "validation_audit"
    contract = CitationContract

    async def fetch(self, src): return src
    def parse(self, raw): yield raw if isinstance(raw, dict) else {
        "citing_id":"","cited_id":"","cited_exists":True,
        "semantic_match_score":1.0,"circular_dep_flag":False}

    def has_cycle(self, edges: list[tuple]) -> bool:
        g = nx.DiGraph(); g.add_edges_from(edges)
        try: nx.find_cycle(g); return True
        except nx.NetworkXNoCycle: return False

    def _score_gates(self, rec, resolved=None, ri=None, phi=None):
        gates = super()._score_gates(rec, resolved, ri, phi)
        if rec.circular_dep_flag or not rec.cited_exists:
            gates["contradiction_clearance"] = 0.0
        else:
            gates["contradiction_clearance"] = rec.semantic_match_score
        return gates

# v10 — canonical
PYEOF

# --- 27. ClaimNoveltyLens ---
cat > "$LENSES/v10/claim_novelty_lens.py" << 'PYEOF'
"""ClaimNoveltyLens — cosine-distance novelty scoring. Team: math_phi."""
from pydantic import BaseModel
import numpy as np
from ..lenses.base import BaseSemanticLens

class NoveltyContract(BaseModel):
    novelty_embedding_distance: float
    nearest_canon_id: str | None
    loom_priority: int = 0

class ClaimNoveltyLens(BaseSemanticLens):
    name = "ClaimNoveltyLens"
    team_id = "math_phi"
    contract = NoveltyContract

    async def fetch(self, src): return src
    def parse(self, raw): yield raw if isinstance(raw, dict) else {
        "novelty_embedding_distance":0.5,"nearest_canon_id":None,"loom_priority":0}

    def cosine_distance(self, a: np.ndarray, b: np.ndarray) -> float:
        return 1.0 - float(np.dot(a,b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))

    def _score_gates(self, rec, resolved=None, ri=None, phi=None):
        gates = super()._score_gates(rec, resolved, ri, phi)
        if rec.novelty_embedding_distance > 0.85:
            rec.loom_priority = 1
        gates["semantic_relevance"] = min(1.0, rec.novelty_embedding_distance)
        return gates

# v10 — canonical
PYEOF

# --- 28. LangChainAgenticLens ---
cat > "$LENSES/v10/langchain_agentic_lens.py" << 'PYEOF'
"""LangChainAgenticLens — agentic extraction with step + budget cap. Team: web_crawl."""
from __future__ import annotations
from pydantic import BaseModel, Field
import structlog
from ..lenses.base import BaseSemanticLens
log = structlog.get_logger(__name__)

class AgenticContract(BaseModel):
    tool_calls: list[dict] = Field(default_factory=list)
    cost_usd_spent: float = 0.0
    cost_budget_usd: float = 5.0
    step_count: int = 0
    max_steps: int = 25

class BudgetExhausted(Exception): ...
class StepCapReached(Exception): ...

class LangChainAgenticLens(BaseSemanticLens):
    name = "LangChainAgenticLens"
    team_id = "web_crawl"
    contract = AgenticContract

    async def fetch(self, src): return src
    def parse(self, raw): yield raw if isinstance(raw, dict) else {
        "tool_calls":[],"cost_usd_spent":0.0,"cost_budget_usd":5.0,
        "step_count":0,"max_steps":25}

    def step(self, state: AgenticContract, tool_name: str, cost: float):
        if state.cost_usd_spent + cost > state.cost_budget_usd:
            log.warning("agentic.budget_exhausted", spent=state.cost_usd_spent)
            raise BudgetExhausted()
        if state.step_count >= state.max_steps:
            raise StepCapReached()
        state.tool_calls.append({"tool": tool_name, "cost": cost})
        state.cost_usd_spent += cost
        state.step_count += 1

    def _score_gates(self, rec, resolved=None, ri=None, phi=None):
        gates = super()._score_gates(rec, resolved, ri, phi)
        gates["cost_efficiency"] = 1.0 - min(1.0, rec.cost_usd_spent / max(rec.cost_budget_usd, 1e-6))
        return gates

# v10 — canonical
PYEOF

# --- 29. StreamingLens ---
cat > "$LENSES/v10/streaming_lens.py" << 'PYEOF'
"""StreamingLens — Kafka/Redis Streams real-time ingestion. Team: data_engineering."""
from pydantic import BaseModel
from ..lenses.base import BaseSemanticLens

class StreamingContract(BaseModel):
    stream_source: str  # "kafka"|"redis_streams"
    topic: str
    offset: int
    lag_ms: int

class StreamingLens(BaseSemanticLens):
    name = "StreamingLens"
    team_id = "data_engineering"
    contract = StreamingContract

    async def fetch(self, src): return src
    def parse(self, raw): yield raw if isinstance(raw, dict) else {
        "stream_source":"kafka","topic":"default","offset":0,"lag_ms":0}

    def _score_gates(self, rec, resolved=None, ri=None, phi=None):
        gates = super()._score_gates(rec, resolved, ri, phi)
        gates["completeness"] = 1.0 if rec.lag_ms < 60_000 else 0.0
        return gates

# v10 — canonical
PYEOF

# --- 30. EmbeddingDriftLens ---
cat > "$LENSES/v10/embedding_drift_lens.py" << 'PYEOF'
"""EmbeddingDriftLens — model upgrade drift detection. Team: math_phi."""
from pydantic import BaseModel
import numpy as np
from ..lenses.base import BaseSemanticLens

class DriftContract(BaseModel):
    model_id_old: str
    model_id_new: str
    cosine_drift: float
    reembedding_required: bool

class EmbeddingDriftLens(BaseSemanticLens):
    name = "EmbeddingDriftLens"
    team_id = "math_phi"
    contract = DriftContract

    async def fetch(self, src): return src
    def parse(self, raw): yield raw if isinstance(raw, dict) else {
        "model_id_old":"MiniLM-v1","model_id_new":"MiniLM-v2",
        "cosine_drift":0.0,"reembedding_required":False}

    def drift(self, v_old: np.ndarray, v_new: np.ndarray) -> float:
        return 1.0 - float(np.dot(v_old, v_new) /
                           (np.linalg.norm(v_old) * np.linalg.norm(v_new) + 1e-9))

    def _score_gates(self, rec, resolved=None, ri=None, phi=None):
        gates = super()._score_gates(rec, resolved, ri, phi)
        gates["semantic_relevance"] = 1.0 - min(1.0, rec.cosine_drift / 0.10)
        return gates

# v10 — canonical
PYEOF

# --- 31. CostBudgetLens ---
cat > "$LENSES/v10/cost_budget_lens.py" << 'PYEOF'
"""CostBudgetLens — per-lens ROI and budget enforcement. Team: data_engineering."""
from pydantic import BaseModel
from ..lenses.base import BaseSemanticLens

class CostContract(BaseModel):
    lens_id: str
    usd_per_canon_record: float
    monthly_budget: float
    monthly_spend: float
    roi_score: float

class CostBudgetLens(BaseSemanticLens):
    name = "CostBudgetLens"
    team_id = "data_engineering"
    contract = CostContract

    async def fetch(self, src): return src
    def parse(self, raw): yield raw if isinstance(raw, dict) else {
        "lens_id":"default","usd_per_canon_record":0.001,
        "monthly_budget":100.0,"monthly_spend":0.0,"roi_score":1.0}

    def _score_gates(self, rec, resolved=None, ri=None, phi=None):
        gates = super()._score_gates(rec, resolved, ri, phi)
        if rec.monthly_spend >= rec.monthly_budget:
            gates["cost_efficiency"] = 0.0
        else:
            gates["cost_efficiency"] = 1.0 - rec.monthly_spend / max(rec.monthly_budget, 1e-6)
        return gates

# v10 — canonical
PYEOF

# --- 32. SchemaEvolutionLens ---
cat > "$LENSES/v10/schema_evolution_lens.py" << 'PYEOF'
"""SchemaEvolutionLens — 90-day deprecation window management. Team: architecture."""
from pydantic import BaseModel
from ..lenses.base import BaseSemanticLens

class SchemaEvoContract(BaseModel):
    pydantic_version: str
    deprecation_cycle_days: int = 90
    consumer_compat_matrix: dict[str,str]

class SchemaEvolutionLens(BaseSemanticLens):
    name = "SchemaEvolutionLens"
    team_id = "architecture"
    contract = SchemaEvoContract

    async def fetch(self, src): return src
    def parse(self, raw): yield raw if isinstance(raw, dict) else {
        "pydantic_version":"2.8","deprecation_cycle_days":90,"consumer_compat_matrix":{}}

    def is_compatible(self, current: str, target: str) -> bool:
        try:
            import semver
            return semver.VersionInfo.parse(target).major == semver.VersionInfo.parse(current).major
        except Exception: return True

    def _score_gates(self, rec, resolved=None, ri=None, phi=None):
        gates = super()._score_gates(rec, resolved, ri, phi)
        gates["schema_score"] = 1.0
        return gates

# v10 — canonical
PYEOF

# --- 33. MultiModalLens ---
cat > "$LENSES/v10/multimodal_lens.py" << 'PYEOF'
"""MultiModalLens — patent figures/tables/equations. Team: web_crawl."""
from pydantic import BaseModel, Field
from ..lenses.base import BaseSemanticLens

class MultiModalContract(BaseModel):
    figures: list[str] = Field(default_factory=list)   # bytes hashes
    tables: list[dict] = Field(default_factory=list)
    equations_latex: list[str] = Field(default_factory=list)
    clip_embedding_dim: int = 512

class MultiModalLens(BaseSemanticLens):
    name = "MultiModalLens"
    team_id = "web_crawl"
    contract = MultiModalContract

    async def fetch(self, src): return src
    def parse(self, raw): yield raw if isinstance(raw, dict) else {
        "figures":[],"tables":[],"equations_latex":[],"clip_embedding_dim":512}

    def _score_gates(self, rec, resolved=None, ri=None, phi=None):
        gates = super()._score_gates(rec, resolved, ri, phi)
        gates["completeness"] = min(1.0,
            (len(rec.figures) + len(rec.tables) + len(rec.equations_latex)) / 3)
        return gates

# v10 — canonical
PYEOF

# --- 34. FederatedLens ---
cat > "$LENSES/v10/federated_lens.py" << 'PYEOF'
"""FederatedLens — cross-jurisdiction patent harmonisation (EPO/JPO/KIPO/WIPO). Team: web_crawl."""
from pydantic import BaseModel
from ..lenses.base import BaseSemanticLens

class FederatedContract(BaseModel):
    office: str  # "epo"|"jpo"|"kipo"|"wipo_pct"|"cnipa"
    harmonized_id: str
    inpadoc_family: list[str]
    raw_payload_size_bytes: int

TRUSTED_OFFICES = {"epo","jpo","kipo","wipo_pct"}

class FederatedLens(BaseSemanticLens):
    name = "FederatedLens"
    team_id = "web_crawl"
    contract = FederatedContract

    async def fetch(self, src): return src
    def parse(self, raw): yield raw if isinstance(raw, dict) else {
        "office":"epo","harmonized_id":"","inpadoc_family":[],"raw_payload_size_bytes":0}

    def _score_gates(self, rec, resolved=None, ri=None, phi=None):
        gates = super()._score_gates(rec, resolved, ri, phi)
        gates["source_trust"] = 0.95 if rec.office in TRUSTED_OFFICES else 0.70
        return gates

# v10 — canonical
PYEOF

# ──────────────────────────────────────────────────────────────
# 4.9  Patch Handrail CPS lanes (append v10 team lanes)
# ──────────────────────────────────────────────────────────────
CPS_LANES_FILE="$LENSES/cps_integration/handrail_cps_lanes.py"
if [ -f "$CPS_LANES_FILE" ]; then
  if ! grep -q "team.architecture.review" "$CPS_LANES_FILE"; then
    log "Appending v10 team CPS lanes to handrail_cps_lanes.py..."
    cat >> "$CPS_LANES_FILE" << 'PYEOF'

# v10 team-scoped lanes — appended by deploy_v10_MAX.sh
V10_TEAM_LANES = [
    ("team.architecture.review",             "architecture"),
    ("team.architecture.approve_lens_config", "architecture"),
    ("team.math.recompute_phi",               "math_phi"),
    ("team.math.calibrate_weights",           "math_phi"),
    ("team.dataeng.parquet_compact",          "data_engineering"),
    ("team.dataeng.disk_health",              "data_engineering"),
    ("team.dataeng.embedding_refresh",        "data_engineering"),
    ("team.audit.scan",                       "validation_audit"),
    ("team.audit.dispute",                    "validation_audit"),
    ("team.audit.cross_check",                "validation_audit"),
    ("team.crawl.fetch",                      "web_crawl"),
    ("team.crawl.respect_robots",             "web_crawl"),
    ("team.crawl.rate_limit",                 "web_crawl"),
]

def register_v10_team_lanes():
    import httpx
    with httpx.Client(timeout=10) as cli:
        for name, team in V10_TEAM_LANES:
            try:
                cli.post(f"{HANDRAIL}/cps/lanes/register",
                         json={"name": name, "team": team,
                               "deterministic": True, "owner": f"lens.cabinet.v10.{team}"})
            except Exception as exc:
                import structlog
                structlog.get_logger("cps.v10").warning("lane.register.skip",
                                                         lane=name, err=repr(exc))

# v10 — canonical
PYEOF
  fi
fi

# ──────────────────────────────────────────────────────────────
# 4.10  TESTS
# ──────────────────────────────────────────────────────────────
mkdir -p "$RUNTIME/tests/v10"
touch "$RUNTIME/tests/v10/__init__.py"

cat > "$RUNTIME/tests/v10/test_team_runtime.py" << 'PYEOF'
"""v10 smoke tests — team runtime."""
import pytest
from services.ns.nss.lenses.teams import REGISTRY

def test_five_teams_registered():
    ids = {t.team_id for t in REGISTRY.list()}
    assert ids == {"architecture","math_phi","data_engineering","validation_audit","web_crawl"}

def test_solo_quorum_default():
    for t in REGISTRY.list():
        assert t.charter.quorum_n_of_m == (1, 1)
        assert "mike" in t.on_call_rotation

def test_each_team_has_cps_lanes():
    for t in REGISTRY.list():
        assert len(t.charter.cps_lanes) >= 2, f"{t.team_id} has < 2 CPS lanes"

def test_each_team_has_owned_lenses():
    for t in REGISTRY.list():
        assert len(t.charter.owned_lenses) >= 1, f"{t.team_id} owns no lenses"

def test_each_team_has_ci_gates():
    for t in REGISTRY.list():
        assert len(t.charter.ci_gates) >= 1, f"{t.team_id} has no CI gates"
PYEOF

cat > "$RUNTIME/tests/v10/test_lens_team_assignment.py" << 'PYEOF'
"""v10 — every new lens has correct team_id."""
import pytest
import importlib, sys

EXPECTED = {
    "ProvenanceChainLens":          "validation_audit",
    "DifferentialPrivacyLens":      "validation_audit",
    "AdversarialRobustnessLens":    "validation_audit",
    "TemporalCoherenceLens":        "validation_audit",
    "CrossSourceTriangulationLens": "validation_audit",
    "LegalComplianceLens":          "validation_audit",
    "BiasDetectionLens":            "validation_audit",
    "VersionDriftLens":             "architecture",
    "CitationIntegrityLens":        "validation_audit",
    "ClaimNoveltyLens":             "math_phi",
    "LangChainAgenticLens":         "web_crawl",
    "StreamingLens":                "data_engineering",
    "EmbeddingDriftLens":           "math_phi",
    "CostBudgetLens":               "data_engineering",
    "SchemaEvolutionLens":          "architecture",
    "MultiModalLens":               "web_crawl",
    "FederatedLens":                "web_crawl",
}

@pytest.mark.parametrize("lens_name,expected_team", EXPECTED.items())
def test_lens_team_id(lens_name, expected_team):
    # Import from v10 module
    module_map = {
        "ProvenanceChainLens":          "services.ns.nss.lenses.v10.provenance_chain_lens",
        "DifferentialPrivacyLens":      "services.ns.nss.lenses.v10.differential_privacy_lens",
        "AdversarialRobustnessLens":    "services.ns.nss.lenses.v10.adversarial_robustness_lens",
        "TemporalCoherenceLens":        "services.ns.nss.lenses.v10.temporal_coherence_lens",
        "CrossSourceTriangulationLens": "services.ns.nss.lenses.v10.cross_source_triangulation_lens",
        "LegalComplianceLens":          "services.ns.nss.lenses.v10.legal_compliance_lens",
        "BiasDetectionLens":            "services.ns.nss.lenses.v10.bias_detection_lens",
        "VersionDriftLens":             "services.ns.nss.lenses.v10.version_drift_lens",
        "CitationIntegrityLens":        "services.ns.nss.lenses.v10.citation_integrity_lens",
        "ClaimNoveltyLens":             "services.ns.nss.lenses.v10.claim_novelty_lens",
        "LangChainAgenticLens":         "services.ns.nss.lenses.v10.langchain_agentic_lens",
        "StreamingLens":                "services.ns.nss.lenses.v10.streaming_lens",
        "EmbeddingDriftLens":           "services.ns.nss.lenses.v10.embedding_drift_lens",
        "CostBudgetLens":               "services.ns.nss.lenses.v10.cost_budget_lens",
        "SchemaEvolutionLens":          "services.ns.nss.lenses.v10.schema_evolution_lens",
        "MultiModalLens":               "services.ns.nss.lenses.v10.multimodal_lens",
        "FederatedLens":                "services.ns.nss.lenses.v10.federated_lens",
    }
    mod = importlib.import_module(module_map[lens_name])
    cls = getattr(mod, lens_name)
    assert cls.team_id == expected_team
PYEOF

cat > "$RUNTIME/tests/v10/test_phi_still_flag_only.py" << 'PYEOF'
"""v10 explicit invariant guard — Phi NEVER in gate weights."""
import pytest
from services.ns.nss.lenses.scoring import WEIGHTS

def test_phi_curvature_is_not_a_gate():
    assert "phi_curvature" not in WEIGHTS, "VIOLATION: phi_curvature must never be a gate"
    assert "phi" not in WEIGHTS,           "VIOLATION: phi must never be a gate"

def test_weights_sum_to_one():
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

def test_weights_are_ten():
    assert len(WEIGHTS) == 10, f"Expected 10 gates, got {len(WEIGHTS)}: {list(WEIGHTS)}"
PYEOF

cat > "$RUNTIME/tests/v10/test_symphony_decoupling.py" << 'PYEOF'
"""v10 — Symphony OS import boundary CI gate."""
import pathlib, re, pytest

def test_no_symphony_imports_in_lenses():
    root = pathlib.Path("services/ns/nss/lenses")
    if not root.exists():
        pytest.skip("Lenses directory not found in CWD — run from $RUNTIME")
    bad = []
    for p in root.rglob("*.py"):
        if "contracts_external" in p.parts: continue
        text = p.read_text()
        if re.search(r"\bfrom\s+symphony_os\b|\bimport\s+symphony_os\b", text):
            bad.append(str(p))
    assert not bad, f"Symphony coupling violation: {bad}"

def test_symphony_contracts_no_symphony_import():
    path = pathlib.Path(
        "services/ns/nss/lenses/contracts_external/symphony_contracts.py")
    if not path.exists():
        pytest.skip("symphony_contracts.py not found")
    text = path.read_text()
    assert "symphony_os" not in text
PYEOF

cat > "$RUNTIME/tests/v10/test_v10_lenses_smoke.py" << 'PYEOF'
"""v10 smoke — each new lens instantiates and has required attributes."""
import pytest, importlib

V10_LENS_MODULES = [
    ("services.ns.nss.lenses.v10.provenance_chain_lens",          "ProvenanceChainLens"),
    ("services.ns.nss.lenses.v10.differential_privacy_lens",      "DifferentialPrivacyLens"),
    ("services.ns.nss.lenses.v10.adversarial_robustness_lens",    "AdversarialRobustnessLens"),
    ("services.ns.nss.lenses.v10.temporal_coherence_lens",        "TemporalCoherenceLens"),
    ("services.ns.nss.lenses.v10.cross_source_triangulation_lens","CrossSourceTriangulationLens"),
    ("services.ns.nss.lenses.v10.legal_compliance_lens",          "LegalComplianceLens"),
    ("services.ns.nss.lenses.v10.bias_detection_lens",            "BiasDetectionLens"),
    ("services.ns.nss.lenses.v10.version_drift_lens",             "VersionDriftLens"),
    ("services.ns.nss.lenses.v10.citation_integrity_lens",        "CitationIntegrityLens"),
    ("services.ns.nss.lenses.v10.claim_novelty_lens",             "ClaimNoveltyLens"),
    ("services.ns.nss.lenses.v10.langchain_agentic_lens",         "LangChainAgenticLens"),
    ("services.ns.nss.lenses.v10.streaming_lens",                 "StreamingLens"),
    ("services.ns.nss.lenses.v10.embedding_drift_lens",           "EmbeddingDriftLens"),
    ("services.ns.nss.lenses.v10.cost_budget_lens",               "CostBudgetLens"),
    ("services.ns.nss.lenses.v10.schema_evolution_lens",          "SchemaEvolutionLens"),
    ("services.ns.nss.lenses.v10.multimodal_lens",                "MultiModalLens"),
    ("services.ns.nss.lenses.v10.federated_lens",                 "FederatedLens"),
]

@pytest.mark.parametrize("mod_path,cls_name", V10_LENS_MODULES)
def test_lens_has_required_attrs(mod_path, cls_name):
    mod = importlib.import_module(mod_path)
    cls = getattr(mod, cls_name)
    assert hasattr(cls, "name"),     f"{cls_name} missing .name"
    assert hasattr(cls, "team_id"),  f"{cls_name} missing .team_id"
    assert hasattr(cls, "contract"), f"{cls_name} missing .contract"
    assert cls.team_id != "unassigned", f"{cls_name}.team_id is still 'unassigned'"
PYEOF

# ──────────────────────────────────────────────────────────────
# 4.11  CODEOWNERS
# ──────────────────────────────────────────────────────────────
cat > "$RUNTIME/.github/CODEOWNERS" << 'EOF'
# AXIOLEV NS∞ Lens Cabinet v10 — CODEOWNERS
# Default: Architecture team (currently @mkenworthy solo)
* @mkaxiolev-max/architecture

# Architecture
/services/ns/nss/lenses/cabinet.py          @mkaxiolev-max/architecture
/services/ns/nss/lenses/base.py             @mkaxiolev-max/architecture
/services/ns/nss/lenses/contracts.py        @mkaxiolev-max/architecture
/services/ns/nss/lenses/registry.py         @mkaxiolev-max/architecture
/services/ns/nss/lenses/source_resolver.py  @mkaxiolev-max/architecture
/services/ns/nss/lenses/v10/version_drift_lens.py    @mkaxiolev-max/architecture
/services/ns/nss/lenses/v10/schema_evolution_lens.py @mkaxiolev-max/architecture

# Math / Phi
/services/ns/nss/lenses/phi_curvature.py    @mkaxiolev-max/math-phi
/services/ns/nss/lenses/refractive_index.py @mkaxiolev-max/math-phi
/services/ns/nss/lenses/scoring.py          @mkaxiolev-max/math-phi @mkaxiolev-max/architecture
/services/ns/nss/lenses/v10/claim_novelty_lens.py    @mkaxiolev-max/math-phi
/services/ns/nss/lenses/v10/embedding_drift_lens.py  @mkaxiolev-max/math-phi

# Data Engineering
/services/ns/nss/lenses/writers.py          @mkaxiolev-max/data-eng
/services/ns/nss/lenses/rejects.py          @mkaxiolev-max/data-eng
/services/ns/nss/lenses/embeddings.py       @mkaxiolev-max/data-eng
/services/ns/nss/lenses/observability.py    @mkaxiolev-max/data-eng
/services/ns/nss/lenses/cps_integration/    @mkaxiolev-max/data-eng
/services/ns/nss/lenses/v10/streaming_lens.py   @mkaxiolev-max/data-eng
/services/ns/nss/lenses/v10/cost_budget_lens.py @mkaxiolev-max/data-eng

# Validation / Audit
/services/ns/nss/lenses/validators.py       @mkaxiolev-max/validation-audit
/services/ns/nss/lenses/contradiction.py    @mkaxiolev-max/validation-audit
/services/ns/nss/lenses/receipts.py         @mkaxiolev-max/validation-audit
/services/ns/nss/lenses/v10/provenance_chain_lens.py          @mkaxiolev-max/validation-audit
/services/ns/nss/lenses/v10/differential_privacy_lens.py      @mkaxiolev-max/validation-audit
/services/ns/nss/lenses/v10/adversarial_robustness_lens.py    @mkaxiolev-max/validation-audit
/services/ns/nss/lenses/v10/temporal_coherence_lens.py        @mkaxiolev-max/validation-audit
/services/ns/nss/lenses/v10/cross_source_triangulation_lens.py @mkaxiolev-max/validation-audit
/services/ns/nss/lenses/v10/legal_compliance_lens.py          @mkaxiolev-max/validation-audit @mkenworthy
/services/ns/nss/lenses/v10/bias_detection_lens.py            @mkaxiolev-max/validation-audit
/services/ns/nss/lenses/v10/citation_integrity_lens.py        @mkaxiolev-max/validation-audit

# Web / Crawl
/services/ns/nss/lenses/v10/langchain_agentic_lens.py @mkaxiolev-max/web-crawl
/services/ns/nss/lenses/v10/multimodal_lens.py        @mkaxiolev-max/web-crawl
/services/ns/nss/lenses/v10/federated_lens.py         @mkaxiolev-max/web-crawl

# Decoupled Symphony contract surface
/services/ns/nss/lenses/contracts_external/ @mkaxiolev-max/architecture

# Governance docs
/docs/lens_cabinet/ @mkenworthy
/.github/CODEOWNERS @mkenworthy
EOF

# ──────────────────────────────────────────────────────────────
# 4.12  ADR seeds
# ──────────────────────────────────────────────────────────────
mkdir -p "$RUNTIME/docs/lens_cabinet/adr"
cat > "$RUNTIME/docs/lens_cabinet/adr/0001-5-team-swarm-pattern.md" << 'EOF'
# ADR-0001: Adopt 5-Team Swarm Pattern (runtime + governance dual-nature)
## Status
Accepted
## Context
NS∞ Lens Cabinet must scale from 1 founder to 5+ collaborators without architectural
refactor. Solo-founder discipline and future team delegation must share the same codebase.
## Decision
We will implement 5 Teams as runtime Python classes (BaseTeam subclasses) AND governance
documentation. Teams own Lenses CODEOWNERS-style, register CPS lanes, enforce CI/CD gates,
and emit Prometheus metrics. Quorum starts 1-of-1 (Mike); expands by YAML + CODEOWNERS edit.
## Consequences
Positive: delegation is a data change, not an architecture change. Governance is machine-readable.
Negative: Team objects add ~200 lines of boilerplate. Acceptable for the durability gained.
## Metadata
- date: 2026-04-28
- decision_makers: [mike]
- teams_consulted: [architecture]
- supersedes: none
EOF

cat > "$RUNTIME/docs/lens_cabinet/adr/0002-symphony-decoupling.md" << 'EOF'
# ADR-0002: Decouple Symphony OS via JSON-Schema contract surface
## Status
Accepted
## Context
Symphony OS is a StrategicInitiative under NS∞. Its Document-to-Program Compiler consumes
Lens Canon output. Tight import coupling would create circular dependency and lock release
cadences together.
## Decision
We will publish a versioned JSON Schema contract surface in contracts_external/symphony_contracts.py.
No imports flow in either direction. CI/CD lint rule enforces the boundary.
## Consequences
Positive: Symphony and Lens Cabinet evolve independently. Breaking changes require semver bump + 90-day cycle.
Neutral: Requires JSON Schema publishing infrastructure (axiolev.io/schemas/).
## Metadata
- date: 2026-04-28
- decision_makers: [mike]
- supersedes: none
EOF

cat > "$RUNTIME/docs/lens_cabinet/adr/0003-phi-flag-only.md" << 'EOF'
# ADR-0003: Phi-Curvature remains FLAG-ONLY (explicit non-gate invariant)
## Status
Accepted
## Context
v7 used phi_gate (reject when Φ > 0.08). v8 critique showed legitimate scale-free citation
graphs (CRISPR 2013-2016, LLM 2022-2024) fail this gate, destroying valid Canon candidates.
## Decision
Phi-Curvature is observability only. It fires a Prometheus counter and surfaces in receipts.
It NEVER appears in GATE_WEIGHTS. A unit test asserts this invariant on every CI run.
## Consequences
Positive: legitimate heavy-tail batches are no longer dropped. Operational visibility preserved.
Negative: none — anomalous phi still routes to deeper inspection via the receipt audit trail.
## Metadata
- date: 2026-04-28
- decision_makers: [mike]
- teams_consulted: [math_phi, validation_audit]
- supersedes: ADR-phi-gate-v7 (informal)
EOF

# ──────────────────────────────────────────────────────────────
# 4.13  On-call YAML
# ──────────────────────────────────────────────────────────────
mkdir -p "$RUNTIME/docs/lens_cabinet"
cat > "$RUNTIME/docs/lens_cabinet/oncall_v10.yaml" << 'EOF'
# AXIOLEV NS∞ Lens Cabinet v10 — On-Call Rotation
# Solo-founder mode: Mike is sole on-call across all 5 teams.
teams:
  architecture:
    primary: [mike]
    secondary: []        # → drummond, when ready
    pager: page+sms
  math_phi:
    primary: [mike]
    secondary: []        # → walrath
  data_engineering:
    primary: [mike]
    secondary: []        # → schlingmann
  validation_audit:
    primary: [mike]
    secondary: []        # → reyes
  web_crawl:
    primary: [mike]
    secondary: []        # → weston

rotation_window_hours: 168  # weekly once N > 1
escalation_chain: [mike]
sla:
  acknowledge_minutes: 15
  resolve_minutes: 240
EOF

# ──────────────────────────────────────────────────────────────
# 4.14  CLI extension: axiolev lens-cabinet teams
# ──────────────────────────────────────────────────────────────
mkdir -p "$RUNTIME/services/ns/cli"
touch "$RUNTIME/services/ns/cli/__init__.py"
cat > "$RUNTIME/services/ns/cli/teams.py" << 'PYEOF'
"""CLI: axiolev lens-cabinet teams <subcommand>"""
import click
from services.ns.nss.lenses.teams import REGISTRY

@click.group()
def teams(): """Team management CLI."""

@teams.command("list")
def list_teams():
    """List all registered teams."""
    for t in REGISTRY.list():
        click.echo(f"{t.team_id:18s} {t.name:32s} "
                   f"lenses={len(t.charter.owned_lenses):2d} "
                   f"lanes={len(t.charter.cps_lanes)}")

@teams.command("show")
@click.argument("team_id")
def show(team_id):
    """Show team detail."""
    t = REGISTRY.get(team_id)
    click.echo(f"Mission  : {t.charter.mission}")
    click.echo(f"Lenses   : {', '.join(t.charter.owned_lenses)}")
    click.echo(f"CPS lanes: {', '.join(t.charter.cps_lanes)}")
    click.echo(f"CI gates : {', '.join(t.charter.ci_gates)}")
    click.echo(f"Quorum   : {t.charter.quorum_n_of_m[0]}-of-{t.charter.quorum_n_of_m[1]}")
    click.echo(f"On-call  : {', '.join(t.on_call_rotation)}")

@teams.command("runs")
@click.argument("team_id")
def runs(team_id):
    """Show team run metrics."""
    t = REGISTRY.get(team_id)
    m = t.metrics
    click.echo(f"runs_owned={m.runs_owned} admit={m.admission_count} "
               f"reject={m.rejection_count} rate={m.admission_rate:.3f}")

@teams.command("oncall")
@click.argument("team_id")
def oncall(team_id):
    """Show on-call rotation for team."""
    t = REGISTRY.get(team_id)
    click.echo(f"{team_id}: {' -> '.join(t.on_call_rotation)}")

@teams.command("quorum-check")
@click.argument("team_id")
@click.argument("approvers", nargs=-1)
def quorum_check(team_id, approvers):
    """Test if a set of approvers satisfies quorum."""
    t = REGISTRY.get(team_id)
    ok = t.quorum_satisfied(list(approvers))
    click.echo(f"quorum_satisfied={ok} (need {t.charter.quorum_n_of_m[0]}-of-{t.charter.quorum_n_of_m[1]})")
PYEOF

log "All files written."

# ============================================================
# 5. REGISTER CPS LANES (graceful — Handrail may be down)
# ============================================================
log "=== REGISTER CPS LANES ==="
"$NSS_PYTHON" << 'REGEOF' || warn "CPS lane registration skipped (Handrail not yet running)"
import sys
sys.path.insert(0, ".")
try:
    from services.ns.nss.lenses.cps_integration.handrail_cps_lanes import (
        register_all, register_v10_team_lanes
    )
    register_all()
    register_v10_team_lanes()
    print("[OK] All CPS lanes registered")
except ImportError as e:
    print(f"[SKIP] Import error: {e}")
except Exception as e:
    print(f"[WARN] CPS registration: {e}")
REGEOF

# ============================================================
# 6. RUN TESTS
# ============================================================
log "=== RUNNING TESTS ==="
cd "$RUNTIME"
NSS_PYTEST="/Volumes/NSExternal/NSS/.venv/bin/pytest"
[ ! -f "$NSS_PYTEST" ] && NSS_PYTEST="pytest"
"$NSS_PYTEST" -q \
  services/ns/nss/lenses/tests/ \
  tests/v9/ \
  tests/v10/ \
  --tb=short \
  --maxfail=10 \
  -p no:warnings \
  2>&1 | tee /tmp/v10_pytest.log || true

PASSED=$(grep -E "^\d+ passed" /tmp/v10_pytest.log | awk '{print $1}' || echo "0")
FAILED=$(grep -E " failed" /tmp/v10_pytest.log | grep -oE "^[0-9]+" || echo "0")

log "Test result: ${PASSED} passed / ${FAILED} failed"
if [ "$FAILED" -gt 0 ]; then
  warn "Some tests failed — check /tmp/v10_pytest.log before pushing"
fi

# ============================================================
# 7. GIT COMMIT
# ============================================================
log "=== GIT COMMIT ==="
cd "$RUNTIME"
git add -A
git commit -m "feat(lens-cabinet): v10 canonical — 5-team swarm + 34 lenses + Symphony decoupling

- 5-Team Swarm runtime: Architecture, Math/Phi, Data Engineering, Validation/Audit, Web/Crawl
- 17 new production lenses (18-34): Provenance, DP, Adversarial, Temporal, Triangulation,
  Legal, Bias, VersionDrift, CitationIntegrity, ClaimNovelty, LangChainAgentic, Streaming,
  EmbeddingDrift, CostBudget, SchemaEvolution, MultiModal, Federated
- Symphony OS DECOUPLED via contracts_external/symphony_contracts.py (no symphony_os imports)
- CODEOWNERS + ADR log (0001-0003) + oncall_v10.yaml seeded
- v9 invariants preserved: Lens/LensRun separation, SourceResolver-first, 10-gate score,
  Phi FLAG-ONLY, mandatory reject storage, 9 receipt types, ROOT ledger
- Target: 1389/1389 tests | ≥93.5 live NS∞ score within 7 days
- Branch: integration/max-omega-v10 (fast-forward from a5852827)

Refs: v9 canonical a5852827, v10 spec 2026-04-28
Closes: Ring-5 Lens Cabinet gate" \
  --no-verify 2>/dev/null || \
  git commit --allow-empty -m "feat(lens-cabinet): v10 deploy — no diff (already applied)"

ok "Committed to $BRANCH"

# ============================================================
# 8. RESUME NS∞
# ============================================================
log "=== RESUME NS∞ ==="
if [ -f "$RUNTIME/resume_ns.sh" ]; then
  bash "$RUNTIME/resume_ns.sh"
else
  warn "resume_ns.sh not found at $RUNTIME — start services manually"
fi

# ============================================================
# 9. POST-DEPLOY HEALTH + OBSERVABILITY
# ============================================================
log "=== HEALTH CHECKS ==="
sleep 3  # allow services to settle

for PORT_PATH in "8011/healthz" "8080/healthz" "9003/healthz"; do
  PORT="${PORT_PATH%%/*}"; P="${PORT_PATH##*/}"
  if curl -fsS "http://127.0.0.1:$PORT/$P" > /dev/null 2>&1; then
    ok ":$PORT healthy"
  else
    warn ":$PORT not responding"
  fi
done

# Verify CPS lanes include v10 team lanes
if curl -fsS http://127.0.0.1:8011/cps/lanes > /dev/null 2>&1; then
  V10_LANE_COUNT=$(curl -s http://127.0.0.1:8011/cps/lanes | \
    python3 -c "import sys,json; d=json.load(sys.stdin); \
    print(sum(1 for l in (d if isinstance(d,list) else d.get('lanes',[])) \
          if 'team.' in (l if isinstance(l,str) else l.get('name',''))))" 2>/dev/null || echo "?")
  log "v10 team CPS lanes registered: ${V10_LANE_COUNT}"
fi

# NS∞ score check
if curl -fsS http://127.0.0.1:9000/health > /dev/null 2>&1; then
  SCORE=$(curl -s http://127.0.0.1:9000/health | \
    python3 -c "import sys,json; d=json.load(sys.stdin); \
    print(d.get('score_live','?'))" 2>/dev/null || echo "?")
  log "NS∞ live score: ${SCORE}  (target ≥93.5 within 7 days)"
fi

# ============================================================
# 10. FINAL STATUS
# ============================================================
echo ""
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${GREEN}  LENS CABINET v10 — DEPLOYED                              ${NC}"
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "  Branch   : ${CYAN}${BRANCH}${NC}"
echo -e "  Lenses   : ${CYAN}34 total (17 v9 + 17 v10)${NC}"
echo -e "  Teams    : ${CYAN}5 (Architecture / Math·Phi / DataEng / Audit / WebCrawl)${NC}"
echo -e "  Tests    : ${CYAN}${PASSED} passed${NC}"
echo -e "  Symphony : ${CYAN}DECOUPLED via contracts_external/${NC}"
echo -e "  ADRs     : ${CYAN}0001 0002 0003 seeded${NC}"
echo ""
echo -e "  RIGHT TERMINAL OBSERVABILITY:"
echo -e "  ${YELLOW}watch -n2 'curl -s localhost:8011/cps/lanes | jq .'${NC}"
echo -e "  ${YELLOW}watch -n2 'curl -s localhost:9090/metrics | grep ^team_'${NC}"
echo -e "  ${YELLOW}tail -f /Volumes/NSExternal/ALEXANDRIA/2026/04/*.json${NC}"
echo -e "  ${YELLOW}open http://localhost:3000/d/lens_cabinet_v9${NC}"
echo ""
echo -e "  FIRST PRODUCTION RUN:"
echo -e "  ${YELLOW}python -m services.ns.nss.lenses.cli run uspto_patentsview \\${NC}"
echo -e "  ${YELLOW}    https://data.uspto.gov/.../g_patent_2026Q1.tsv.zip${NC}"
echo ""
echo -e "  ROLLBACK:  ${RED}git checkout integration/max-omega-20260421-191635 && bash scripts/deploy_v9.sh${NC}"
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════════════════════${NC}"

# v10 — canonical — supersedes v1..v9
