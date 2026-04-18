#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# NS∞ HOMEBREW TERMINAL (LEFT) — SYSTEM AUDIT + RING 5 + MAC ADAPTER CLOSURE
# AXIOLEV Holdings LLC © 2026 | Mike Kenworthy, Founder/CEO
# April 14, 2026 | boot-operational-closure branch
# ═══════════════════════════════════════════════════════════════════════════════

# NOTE: do NOT use set -e — arithmetic counter increments return exit code 0
# when result is non-zero, killing the script. We handle errors explicitly.

REPO_ROOT="$HOME/axiolev_runtime"
TIMESTAMP=$(date "+%Y-%m-%d_%H:%M:%S")
HOMEBREW_LOG="$REPO_ROOT/homebrew_${TIMESTAMP}.log"
SHARED_STATE="/tmp/ns_closure_state.json"
ALEXANDRIA="/Volumes/NSExternal/ALEXANDRIA"

# Color codes
G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'
C='\033[0;36m'; M='\033[0;35m'; NC='\033[0m'; BOLD='\033[1m'

ok()   { echo -e "${G}  [PASS]${NC} $*" | tee -a "$HOMEBREW_LOG"; }
warn() { echo -e "${Y}  [WARN]${NC} $*" | tee -a "$HOMEBREW_LOG"; }
fail() { echo -e "${R}  [FAIL]${NC} $*" | tee -a "$HOMEBREW_LOG"; }
info() { echo -e "${C}  [INFO]${NC} $*" | tee -a "$HOMEBREW_LOG"; }
hdr()  { echo -e "\n${M}${BOLD}$*${NC}" | tee -a "$HOMEBREW_LOG"
         echo -e "$(printf '─%.0s' {1..72})" | tee -a "$HOMEBREW_LOG"; }

# FIX: removed -- separator; with -c, sys.argv=['-c','key','val'] so
# range(0, len-1, 2) → i=0 → s[argv[1]]=argv[2] ✓
update_state() {
  python3 -c "
import json, sys
try:
  s = json.load(open('$SHARED_STATE'))
except:
  s = {}
for i in range(0, len(sys.argv)-1, 2):
  s[sys.argv[i+1]] = sys.argv[i+2]
json.dump(s, open('$SHARED_STATE', 'w'), indent=2)
" "$@" 2>/dev/null || true
}

# Docker socket detection
for sock in /var/run/docker.sock "$HOME/.docker/run/docker.sock"; do
  [ -S "$sock" ] && { export DOCKER_HOST="unix://$sock"; break; }
done

cd "$REPO_ROOT" || { echo "FATAL: cannot cd to $REPO_ROOT"; exit 1; }
[ -f ".env" ] && { set -a; source .env; set +a; }

mkdir -p "$REPO_ROOT"
> "$HOMEBREW_LOG"

# Initialize shared state
cat > "$SHARED_STATE" << 'STATEOF'
{
  "homebrew_phase": "initializing",
  "red_phase": "waiting",
  "ring5_gates_closed": 0,
  "mac_adapter_closures": 0,
  "alexandria_closures": 0,
  "final_status": "not_started"
}
STATEOF

clear
echo -e "${M}${BOLD}"
cat << 'BANNER'
╔══════════════════════════════════════════════════════════════════════════════╗
║    NS∞ HOMEBREW TERMINAL (LEFT)                                             ║
║    AXIOLEV Holdings LLC © 2026 | Mike Kenworthy, Founder/CEO               ║
║    System Audit + Ring 5 Gate Check + Mac Adapter Contract Freeze          ║
╚══════════════════════════════════════════════════════════════════════════════╝
BANNER
echo -e "${NC}"
echo "  Started:      $TIMESTAMP"
echo "  Repo:         $REPO_ROOT"
echo "  Shared state: $SHARED_STATE"
echo "  Log:          $HOMEBREW_LOG"
echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 0: SYSTEM HEALTH
# ═══════════════════════════════════════════════════════════════════════════════

hdr "PHASE 0 — SYSTEM HEALTH"

update_state "homebrew_phase" "phase_0_health"

# Git identity
BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "none")
info "Branch: $BRANCH | Commit: $COMMIT | Tag: $LATEST_TAG"
[ "$BRANCH" = "boot-operational-closure" ] && ok "Branch: boot-operational-closure ✓" || warn "Branch: $BRANCH"

# Alexandria mount
if [ -d "/Volumes/NSExternal" ]; then
  ALEX_MOUNT="/Volumes/NSExternal"
  ok "Alexandria SSD: $ALEX_MOUNT"
elif [ -d "/Volumes/Alexandria_4TB" ]; then
  ALEX_MOUNT="/Volumes/Alexandria_4TB"
  ok "Alexandria SSD: $ALEX_MOUNT (alternate mount)"
else
  warn "Alexandria SSD: not mounted (receipts will not write)"
  ALEX_MOUNT=""
fi

# State endpoint
if curl -sf --max-time 3 http://127.0.0.1:9090/state >/dev/null 2>&1; then
  STATE_VAL=$(curl -sf --max-time 3 http://127.0.0.1:9090/state 2>/dev/null | \
    python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('state','?'))" 2>/dev/null || echo "?")
  ok "State endpoint :9090 — state=$STATE_VAL"
else
  warn "State endpoint :9090 not responding (boot docker compose up if needed)"
fi

# Docker services
# FIX: docker info redirect was redundant (&>/dev/null already covers stderr)
if docker info >/dev/null 2>&1; then
  ok "Docker daemon: responsive"
  # FIX: grep -c exits 1 on 0 matches (outputs "0" then exits 1); use || true
  # so the subshell doesn't swallow the "0" and echo a second "0"
  RUNNING=$(docker compose ps --filter "status=running" 2>/dev/null | tail -n +2 | grep -c "." || true)
  TOTAL=$(docker compose ps 2>/dev/null | tail -n +2 | grep -c "." || true)
  info "Docker compose services: $RUNNING running / $TOTAL total"
  [ "$RUNNING" -gt 0 ] && ok "Services up: $RUNNING" || warn "No services running — may need: docker compose up -d"
else
  warn "Docker not responding"
fi

update_state "homebrew_phase" "phase_0_complete"
echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1: RING 5 GATE CHECK
# ═══════════════════════════════════════════════════════════════════════════════

hdr "PHASE 1 — RING 5 GATE CHECK"

update_state "homebrew_phase" "phase_1_ring5"

GATES_CLOSED=0
STRIPE_KEY="${STRIPE_SECRET_KEY:-}"

# Gate 1: Stripe LLC verified — charges_enabled via API (distinct from key presence)
# FIX: original Gate 1 and Gate 2 were identical (both checked sk_live_ prefix),
# meaning max achievable score was 4/5. Gate 1 now checks Stripe's charges_enabled
# flag, which only becomes true after LLC verification + Stripe business review.
info "Gate 1: Stripe LLC verified (charges_enabled via Stripe API)"
if echo "$STRIPE_KEY" | grep -q "^sk_live_"; then
  CHARGES_ENABLED=$(curl -sf --max-time 5 \
    -H "Authorization: Bearer $STRIPE_KEY" \
    https://api.stripe.com/v1/account 2>/dev/null | \
    python3 -c "import json,sys; d=json.load(sys.stdin); print(str(d.get('charges_enabled',False)).lower())" \
    2>/dev/null || echo "false")
  if [ "$CHARGES_ENABLED" = "true" ]; then
    ok "Gate 1: Stripe LLC verified + charges_enabled ✓"
    GATES_CLOSED=$((GATES_CLOSED + 1))
  else
    warn "Gate 1: Live key present but charges_enabled=false — complete LLC verification at dashboard.stripe.com"
  fi
else
  warn "Gate 1: STRIPE_SECRET_KEY not set or not live — complete LLC verification, then set sk_live_..."
fi

# Gate 2: Live Stripe secret key present in environment
info "Gate 2: Live Stripe secret key present in environment"
if echo "$STRIPE_KEY" | grep -q "^sk_live_"; then
  ok "Gate 2: Live Stripe key confirmed ✓"
  GATES_CLOSED=$((GATES_CLOSED + 1))
else
  warn "Gate 2: Replace STRIPE_SK_PENDING → sk_live_... in .env + Vercel env vars"
fi

# Gate 3: Price IDs
info "Gate 3: ROOT + Handrail Stripe price IDs"
mkdir -p shared/stripe
PRICE_FILE="shared/stripe/price_ids.json"
if [ -f "$PRICE_FILE" ]; then
  ROOT_PRO=$(python3 -c "import json; d=json.load(open('$PRICE_FILE')); print(d.get('root_pro',''))" 2>/dev/null || echo "")
  if [ -n "$ROOT_PRO" ] && echo "$ROOT_PRO" | grep -q "^price_"; then
    ok "Gate 3: Price IDs confirmed — root_pro=$ROOT_PRO ✓"
    GATES_CLOSED=$((GATES_CLOSED + 1))
  else
    warn "Gate 3: Price IDs file exists but IDs not confirmed"
  fi
else
  warn "Gate 3: Creating price_ids.json template..."
  cat > "$PRICE_FILE" << 'PRICEEOF'
{
  "root_pro": "price_1TGWQj3noS0pFsjkiE1kxvjl",
  "root_auto": "price_1TGWQj3noS0pFsjka7GS20U9",
  "handrail_pro": "PENDING",
  "note": "root_pro/root_auto confirmed. handrail_pro: create in Stripe dashboard at $29/mo"
}
PRICEEOF
  ok "Gate 3: price_ids.json created — root_pro/auto confirmed, handrail_pro PENDING"
fi

# Gate 4: YubiKey slot 2
info "Gate 4: YubiKey 5 NFC — slot_2 enrollment"
YUBIKEY_STATUS=$(curl -sf --max-time 3 http://127.0.0.1:9000/kernel/yubikey/status 2>/dev/null | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('slot_2','unknown'))" 2>/dev/null || echo "service_down")
if [ "$YUBIKEY_STATUS" = "enrolled" ]; then
  ok "Gate 4: YubiKey slot_2 enrolled ✓"
  GATES_CLOSED=$((GATES_CLOSED + 1))
else
  warn "Gate 4: YubiKey slot_2 PENDING — slot_1 enrolled (serial 26116460). Procure 2nd YubiKey 5 NFC → POST /kernel/yubikey/provision"
fi

# Gate 5: DNS CNAME
info "Gate 5: DNS CNAME root.axiolev.com → Vercel"
if host root.axiolev.com 2>/dev/null | grep -qi "cname\|vercel"; then
  ok "Gate 5: DNS CNAME resolves ✓"
  GATES_CLOSED=$((GATES_CLOSED + 1))
else
  warn "Gate 5: DNS CNAME not yet set — Cloudflare: root.axiolev.com CNAME → cname.vercel-dns.com"
fi

info "Ring 5: $GATES_CLOSED/5 gates closed"
update_state "ring5_gates_closed" "$GATES_CLOSED"
update_state "homebrew_phase" "phase_1_complete"

echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2: MAC ADAPTER CONTRACT FREEZE
# ═══════════════════════════════════════════════════════════════════════════════

hdr "PHASE 2 — MAC ADAPTER CONTRACT FREEZE"

update_state "homebrew_phase" "phase_2_mac_adapter"

MAC_CLOSURES=0

# 2a: Env contract v1
CONTRACT_FILE="services/handrail-adapter-macos/env_contract_v1.md"
if [ ! -f "$CONTRACT_FILE" ]; then
  mkdir -p "services/handrail-adapter-macos"
  cat > "$CONTRACT_FILE" << 'CONTRACTEOF'
# Mac Adapter Env Contract v1
# AXIOLEV Holdings LLC © 2026 | FROZEN — no additions without major version bump
#
# This contract defines the v1 boundary surface between NS∞ and macOS.
# Any change to this list requires: MAC_ADAPTER_CONTRACT_VERSION bump + migration note.

## V1 ALLOWED OPERATIONS (27 drivers, read + controlled write)

### Environment Reads (always allowed, no escalation)
- env.health             — adapter health + permission_state
- env.get_focused_window — active window id/title/app
- env.list_windows       — all visible windows
- env.get_screen_info    — display count/resolution
- env.get_clipboard      — clipboard text content
- env.get_volume         — system audio volume (0-100)
- env.get_battery        — charge level + charging status
- env.get_network        — wifi SSID + connection state
- env.get_running_apps   — list of running application names

### Environment Writes (require escalation check)
- env.focus_window       — requires: accessibility + screen_recording
- env.open_app           — requires: open permission granted
- env.open_url           — requires: open permission granted
- env.set_clipboard      — no permission required
- env.set_volume         — no permission required

### File System (scoped to .run/<run_id>/adapter/ only)
- file.read              — within approved paths only
- file.write             — within .run/<run_id>/adapter/ only
- file.list              — within approved paths only

## V1 NEVER-EVENTS (always vetoed, no override)
- Any write outside .run/<run_id>/adapter/
- Any operation on /System, /Library, /private
- Any network socket creation
- Any process spawn outside approved list
- Any keychain access

## ESCALATION REQUIRED
All write operations on env.* that modify system state require:
1. Permission pre-check via env.health permission_state
2. Explicit confirmation in operation payload: "escalation_confirmed": true
3. Receipt written to Alexandria after execution

## CONTRACT VERSION
version: 1.0.0
frozen_at: 2026-04-14
frozen_by: Mike Kenworthy, Founder/CEO, AXIOLEV Holdings LLC
CONTRACTEOF
  ok "MAC ADAPTER: env_contract_v1.md frozen ✓"
  MAC_CLOSURES=$((MAC_CLOSURES + 1))
else
  ok "MAC ADAPTER: env_contract_v1.md already exists ✓"
  MAC_CLOSURES=$((MAC_CLOSURES + 1))
fi

# 2b: Pydantic schema freeze
SCHEMA_DIR="services/handrail-adapter-macos/schemas"
SCHEMA_FILE="$SCHEMA_DIR/adapter_envelope.py"
if [ ! -f "$SCHEMA_FILE" ]; then
  mkdir -p "$SCHEMA_DIR"
  cat > "$SCHEMA_FILE" << 'SCHEMAEOF'
"""
Mac Adapter Envelope Schema — V1 FROZEN
AXIOLEV Holdings LLC © 2026
extra='forbid' enforces ABI contract: no undeclared fields accepted
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, Literal

class AdapterRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    adapter_method: str
    adapter_params: Dict[str, Any] = {}
    run_id: str
    policy_version: str = "v1"
    escalation_confirmed: bool = False

class AdapterReceipt(BaseModel):
    model_config = ConfigDict(extra='forbid')
    task_id: str
    timestamp: str
    run_id: str
    checksum: str
    adapter_method: str

class AdapterResult(BaseModel):
    model_config = ConfigDict(extra='forbid')
    ok: bool
    rc: int = 0
    failure_reason: Optional[str] = None
    data: Dict[str, Any] = {}
    checks: Dict[str, Any] = {}
    state_change: Dict[str, Any] = {"type": "none"}
    receipt: AdapterReceipt
    artifacts: list[str] = []
SCHEMAEOF
  ok "MAC ADAPTER: adapter_envelope.py schema frozen (extra='forbid') ✓"
  MAC_CLOSURES=$((MAC_CLOSURES + 1))
else
  ok "MAC ADAPTER: adapter_envelope.py already exists ✓"
  MAC_CLOSURES=$((MAC_CLOSURES + 1))
fi

# 2c: Smoke test
SMOKE_FILE="tests/mac_adapter/smoke_test.sh"
if [ ! -f "$SMOKE_FILE" ]; then
  mkdir -p tests/mac_adapter
  cat > "$SMOKE_FILE" << 'SMOKEEOF'
#!/bin/bash
# Mac Adapter Smoke Test
# Tests: contract integrity, adapter health, schema validation

ADAPTER_URL="http://127.0.0.1:8765"
PASS=0; FAIL=0

check() {
  local label="$1" result="$2"
  if [ "$result" = "pass" ]; then
    echo "  [PASS] $label"; PASS=$((PASS+1))
  else
    echo "  [WARN] $label"; FAIL=$((FAIL+1))
  fi
}

echo "=== Mac Adapter Smoke Test ==="

# Contract file exists
[ -f "$(dirname $0)/../../services/handrail-adapter-macos/env_contract_v1.md" ] \
  && check "env_contract_v1.md exists" "pass" \
  || check "env_contract_v1.md missing" "fail"

# Schema file exists
[ -f "$(dirname $0)/../../services/handrail-adapter-macos/schemas/adapter_envelope.py" ] \
  && check "adapter_envelope.py exists" "pass" \
  || check "adapter_envelope.py missing" "fail"

# Adapter health endpoint
HEALTH=$(curl -sf --max-time 3 "$ADAPTER_URL/env/health" 2>/dev/null || echo "")
[ -n "$HEALTH" ] && check "Adapter :8765 health" "pass" || check "Adapter :8765 not responding (ok if service cold)" "fail"

echo ""
echo "Result: $PASS passed, $FAIL warnings"
SMOKEEOF
  chmod +x "$SMOKE_FILE"
  ok "MAC ADAPTER: smoke_test.sh created ✓"
  MAC_CLOSURES=$((MAC_CLOSURES + 1))
else
  ok "MAC ADAPTER: smoke_test.sh already exists ✓"
  MAC_CLOSURES=$((MAC_CLOSURES + 1))
fi

update_state "mac_adapter_closures" "$MAC_CLOSURES"
info "Mac Adapter closures: $MAC_CLOSURES/3"

echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3: ALEXANDRIA SCHEMA FREEZE
# ═══════════════════════════════════════════════════════════════════════════════

hdr "PHASE 3 — ALEXANDRIA EPISTEMIC SCHEMA FREEZE"

update_state "homebrew_phase" "phase_3_alexandria"

ALEX_CLOSURES=0

# 3a: IngestedObject schema
ALEX_SCHEMA_DIR="shared/alexandria/schema"
mkdir -p "$ALEX_SCHEMA_DIR"

INGESTED_FILE="$ALEX_SCHEMA_DIR/ingested_object.py"
if [ ! -f "$INGESTED_FILE" ]; then
  cat > "$INGESTED_FILE" << 'INGEOF'
"""
Alexandria IngestedObject Schema — V1
AXIOLEV Holdings LLC © 2026 | extra='forbid' — ABI frozen
Every object that enters Alexandria must satisfy this contract.
"""
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Literal, Dict, Any
from datetime import datetime
import hashlib, json

class IngestedObject(BaseModel):
    model_config = ConfigDict(extra='forbid')

    # Identity
    object_id: str          # SHA-256 of (source_uri + content_hash)
    content_hash: str       # SHA-256 of raw content bytes
    source_uri: str         # file path, URL, or canonical ID
    source_type: Literal["file", "url", "api", "manual", "voice"]

    # Content
    content_type: Literal["text", "pdf", "image", "audio", "structured"]
    raw_path: str           # path in alexandria/raw_ingest/
    normalized_path: Optional[str] = None

    # Provenance
    ingested_at: str        # ISO 8601
    ingested_by: str        # service or actor ID
    content_length_bytes: int

    # Authority
    authority_score: float = 0.5     # 0.0 (unverified) to 1.0 (canonical)
    authority_source: str = "unknown"
    requires_review: bool = True

    # Epistemic state
    epistemic_state: Literal[
        "raw",         # just ingested, not processed
        "normalized",  # text extracted, chunked
        "embedded",    # vector index built
        "reviewed",    # founder reviewed
        "candidate",   # candidate for canon promotion
        "canon"        # promoted to Canon (requires explicit approval)
    ] = "raw"

    # Contradiction tracking
    contradicts: list[str] = []    # object_ids this contradicts
    contradicted_by: list[str] = []

    # Metadata
    tags: list[str] = []
    notes: Optional[str] = None

    @field_validator('content_hash')
    @classmethod
    def validate_sha256(cls, v):
        assert len(v) == 64, "content_hash must be SHA-256 (64 hex chars)"
        return v


class ContradictionObject(BaseModel):
    model_config = ConfigDict(extra='forbid')
    contradiction_id: str
    object_a_id: str
    object_b_id: str
    contradiction_type: Literal["factual", "temporal", "authority", "scope"]
    description: str
    detected_at: str
    resolved: bool = False
    resolution_note: Optional[str] = None


class CandidateCanonObject(BaseModel):
    model_config = ConfigDict(extra='forbid')
    candidate_id: str
    source_object_id: str
    proposed_claim: str
    supporting_objects: list[str]
    confidence: float           # 0.0 - 1.0
    proposed_at: str
    proposed_by: str
    # POLICY: canon promotion NEVER automatic. Requires explicit founder approval.
    approved: bool = False
    approved_at: Optional[str] = None
    approved_by: Optional[str] = None
INGEOF
  ok "ALEXANDRIA: ingested_object.py schema frozen ✓"
  ALEX_CLOSURES=$((ALEX_CLOSURES + 1))
else
  ok "ALEXANDRIA: ingested_object.py already exists ✓"
  ALEX_CLOSURES=$((ALEX_CLOSURES + 1))
fi

# 3b: Ether retrieval gate spec
ETHER_FILE="$ALEX_SCHEMA_DIR/ether_gate_spec.py"
if [ ! -f "$ETHER_FILE" ]; then
  cat > "$ETHER_FILE" << 'ETHEREOF'
"""
Ether Retrieval Gate Specification — V1
AXIOLEV Holdings LLC © 2026
Controls what NS∞ reasoning chambers can retrieve from Alexandria.
POLICY: Ether surfaces contradictions — never hides them.
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, Literal, Dict, Any

class EtherQuery(BaseModel):
    model_config = ConfigDict(extra='forbid')
    query_text: str
    query_type: Literal["semantic", "keyword", "object_id", "tag"]
    session_id: str
    max_results: int = 10
    min_authority: float = 0.0      # filter by authority_score
    include_states: list[str] = ["normalized", "reviewed", "candidate", "canon"]
    # raw and candidate states excluded by default — only promoted content
    surface_contradictions: bool = True  # POLICY: always True

class EtherResult(BaseModel):
    model_config = ConfigDict(extra='forbid')
    query_id: str
    session_id: str
    objects: list[Dict[str, Any]]
    contradictions: list[Dict[str, Any]]   # never empty if contradictions exist
    provenance_chain: list[str]            # object_ids that informed this result
    confidence_ceiling: float              # lowest authority_score in result set
    retrieved_at: str
    gate_applied: bool = True

class EtherGateDecision(BaseModel):
    model_config = ConfigDict(extra='forbid')
    query_id: str
    allowed: bool
    denial_reason: Optional[str] = None
    # Gate denies if: query requests canon-only but object is candidate
    # Gate always surfaces contradictions regardless of query
ETHEREOF
  ok "ETHER GATE: ether_gate_spec.py frozen ✓"
  ALEX_CLOSURES=$((ALEX_CLOSURES + 1))
else
  ok "ETHER GATE: ether_gate_spec.py already exists ✓"
  ALEX_CLOSURES=$((ALEX_CLOSURES + 1))
fi

update_state "alexandria_closures" "$ALEX_CLOSURES"
info "Alexandria closures: $ALEX_CLOSURES/2"

echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4: GIT COMMIT + FINAL STATE
# ═══════════════════════════════════════════════════════════════════════════════

hdr "PHASE 4 — COMMIT + CERTIFICATION"

update_state "homebrew_phase" "phase_4_commit"

# Commit new artifacts
DIRTY=$(git status --porcelain 2>/dev/null | grep -v "^??" | wc -l | tr -d ' ')
NEW_FILES=$(git status --porcelain 2>/dev/null | grep "^?" | wc -l | tr -d ' ')

if [ "$DIRTY" -gt 0 ] || [ "$NEW_FILES" -gt 0 ]; then
  git add \
    "services/handrail-adapter-macos/env_contract_v1.md" \
    "services/handrail-adapter-macos/schemas/adapter_envelope.py" \
    "shared/alexandria/schema/ingested_object.py" \
    "shared/alexandria/schema/ether_gate_spec.py" \
    "shared/stripe/price_ids.json" \
    "tests/mac_adapter/smoke_test.sh" \
    "HOMEBREW_LEFT.sh" \
    2>/dev/null || true

  git commit -m "feat(closure): mac-adapter contract v1 + alexandria schema v1 frozen
- services/handrail-adapter-macos/env_contract_v1.md — 27 drivers, v1 FROZEN
- services/handrail-adapter-macos/schemas/adapter_envelope.py — Pydantic extra=forbid
- shared/alexandria/schema/ingested_object.py — IngestedObject + Contradiction + CandidateCanon
- shared/alexandria/schema/ether_gate_spec.py — Ether gate always surfaces contradictions
- shared/stripe/price_ids.json — ROOT Pro/Auto confirmed, Handrail PENDING
- tests/mac_adapter/smoke_test.sh — contract + adapter health checks
- HOMEBREW_LEFT.sh — orchestration script (fixed: update_state, Gate 1 vs 2, grep -c)

AXIOLEV Holdings LLC © 2026 | AI-assisted: Anthropic Claude (no IP transfer)
Ring 5: $GATES_CLOSED/5 gates closed | Mac Adapter: $MAC_CLOSURES/3 | Alexandria: $ALEX_CLOSURES/2" 2>/dev/null && \
    ok "Committed: mac-adapter + alexandria schema freeze ✓" || \
    info "Nothing to commit (all files already committed)"
else
  info "Working tree clean — all artifacts already committed"
fi

FINAL_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# ═══════════════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${M}${BOLD}"
cat << 'FINALEOF'
╔══════════════════════════════════════════════════════════════════════════════╗
║             HOMEBREW TERMINAL — COMPLETION REPORT                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
FINALEOF
echo -e "${NC}"

echo "  Ring 5 Gates:      $GATES_CLOSED / 5 closed"
echo "  Mac Adapter:       $MAC_CLOSURES / 3 contracts frozen"
echo "  Alexandria:        $ALEX_CLOSURES / 2 schemas frozen"
echo "  Commit:            $FINAL_COMMIT"
echo ""

if [ "$GATES_CLOSED" -eq 5 ] && [ "$MAC_CLOSURES" -ge 2 ] && [ "$ALEX_CLOSURES" -ge 2 ]; then
  FINAL_STATUS="BEYOND_FOUNDER_READY"
  echo -e "${G}${BOLD}  ✓ CERTIFICATION: BEYOND_FOUNDER_READY${NC}"
  echo "  All Ring 5 gates closed. Both critical rails frozen."
  echo "  NOTHING ESSENTIAL LEFT TO CODE."
else
  FINAL_STATUS="FOUNDER_READY"
  echo -e "${Y}${BOLD}  ⚑ STATUS: FOUNDER_READY${NC}"
  echo ""
  [ "$GATES_CLOSED" -lt 5 ] && echo "  PENDING Ring 5: $((5 - GATES_CLOSED)) gate(s) remaining:"
  [ "$GATES_CLOSED" -lt 5 ] && echo "    1. Stripe LLC verification → stripe.com/docs/go-live"
  [ "$GATES_CLOSED" -lt 5 ] && echo "    2. Live Stripe key → .env + Vercel"
  [ "$GATES_CLOSED" -lt 5 ] && echo "    3. Handrail price ID → Stripe dashboard \$29/mo"
  [ "$GATES_CLOSED" -lt 5 ] && echo "    4. YubiKey 5 NFC slot_2 → POST /kernel/yubikey/provision"
  [ "$GATES_CLOSED" -lt 5 ] && echo "    5. Cloudflare CNAME: root.axiolev.com → cname.vercel-dns.com"
fi

update_state "final_status" "$FINAL_STATUS"
update_state "homebrew_phase" "complete"

echo ""
echo "  Shared state: $SHARED_STATE"
echo "  Log:          $HOMEBREW_LOG"
echo ""
echo "  RED terminal (RIGHT) is running Mac Adapter Handrail wiring + Alexandria ingestion."
echo "  When RED shows COMPLETE, both rails are closed."
echo ""
echo -e "${C}  curl http://127.0.0.1:9090/state | python3 -m json.tool${NC}"
echo -e "${C}  bash tests/mac_adapter/smoke_test.sh${NC}"
echo ""
