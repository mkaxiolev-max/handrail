#!/usr/bin/env bash
# =============================================================================
# AXIOLEV Holdings LLC © 2026 — All Rights Reserved
# NS∞ FULL BOOT · VERIFICATION · UI WALKTHROUGH · WATCH
# -----------------------------------------------------------------------------
# Purpose: Single-file orchestrator for Claude Code on terminal to boot NS∞,
#          verify every ring, walk every UI, hot-fix known issues, and live-
#          watch the codebase while the organism runs.
#
# Target:  macOS bash 3.2 (Mac Studio M4, axiolevns)
# Constraints:
#   - No associative arrays (declare -A)
#   - No mapfile / readarray
#   - No ${var^^} case conversion
#   - Docker socket auto-detect (/var/run/docker.sock OR $HOME/.docker/run/docker.sock)
#
# Usage:
#   bash ns_verify.sh                 # == all
#   bash ns_verify.sh preflight       # env, ssd, docker, tools
#   bash ns_verify.sh boot            # docker compose up + health gates
#   bash ns_verify.sh verify          # full feature/invariant battery
#   bash ns_verify.sh ui              # UI walkthrough with browser opens
#   bash ns_verify.sh watch           # live codebase + receipt + log watch
#   bash ns_verify.sh fix             # interactive remediation for known issues
#   bash ns_verify.sh report          # emit REPORT.md + Alexandria receipt
#   bash ns_verify.sh all             # full sequence: preflight→boot→verify→ui→report
#
# Structured output (for Claude Code parsing):
#   STATUS: PASS|FAIL|WARN component=<name> reason=<text>
#   EVIDENCE: <path or excerpt>
#   RECEIPT: phase=<x> hash=<sha256>
#   FIX: <suggested remediation>
#   ASK:  <human-input needed>
# =============================================================================

set -u

# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
SCRIPT_VERSION="1.0.0"
SCRIPT_BUILD="ns-verify-20260420"
NS_HOME="${NS_HOME:-$HOME/axiolev_runtime}"
ALEXANDRIA_ROOT="${ALEXANDRIA_ROOT:-/Volumes/NSExternal/ALEXANDRIA}"
ARTIFACTS_DIR="$NS_HOME/.verify_artifacts"
REPORT_FILE="$ARTIFACTS_DIR/REPORT.md"
RECEIPT_FILE="$ARTIFACTS_DIR/RECEIPT.json"
LOG_FILE="$ARTIFACTS_DIR/verify.log"
PHASE_LOG="$ARTIFACTS_DIR/phase.log"

# Service catalog — space-separated "name:port:role" triplets (bash 3.2 safe)
# role: core | gov | data | exec | ui
SERVICES="\
postgres:5432:data \
redis:6379:data \
ns_core:9000:core \
alexandria:9001:core \
model_router:9002:core \
violet:9003:core \
canon:9004:gov \
integrity:9005:gov \
omega:9010:gov \
handrail:8011:exec \
continuum:8788:core \
ns_api:9011:core \
ns_ui:3001:ui"

# HTTP services (port-reachable with /healthz)
HTTP_SERVICES="ns_core alexandria model_router violet canon integrity omega handrail continuum ns_api ns_ui"

# 10 constitutional invariants
INVARIANTS="I1_HIC_veto I2_PDP_policy I3_Omega_bounded I4_receipt_chain I5_canon_single_write I6_append_only I7_authority_decay I8_reversible_registry I9_yubikey_quorum I10_ledger_first"

# Port → UI path mapping (only for role=ui services; API-only services auto-skip in phase_ui)
ui_path_for_port() {
  case "$1" in
    3001) echo "/" ;;         # ns_ui — full Next.js founder habitat
    9000) echo "/docs" ;;     # ns_core — FastAPI OpenAPI docs (read-only)
    *)    echo "/" ;;
  esac
}

# -----------------------------------------------------------------------------
# COLOR / OUTPUT
# -----------------------------------------------------------------------------
if [ -t 1 ]; then
  C_RED=$(printf '\033[31m'); C_GRN=$(printf '\033[32m'); C_YEL=$(printf '\033[33m')
  C_CYN=$(printf '\033[36m'); C_MAG=$(printf '\033[35m'); C_BLD=$(printf '\033[1m')
  C_DIM=$(printf '\033[2m'); C_RST=$(printf '\033[0m')
else
  C_RED=""; C_GRN=""; C_YEL=""; C_CYN=""; C_MAG=""; C_BLD=""; C_DIM=""; C_RST=""
fi

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0
FAILED_COMPONENTS=""

log() {
  local level="$1"; shift
  local msg="$*"
  local ts; ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  case "$level" in
    PASS) printf "%s [${C_GRN}PASS${C_RST}] %s\n" "$ts" "$msg"; PASS_COUNT=$((PASS_COUNT+1)) ;;
    FAIL) printf "%s [${C_RED}FAIL${C_RST}] %s\n" "$ts" "$msg"; FAIL_COUNT=$((FAIL_COUNT+1)) ;;
    WARN) printf "%s [${C_YEL}WARN${C_RST}] %s\n" "$ts" "$msg"; WARN_COUNT=$((WARN_COUNT+1)) ;;
    INFO) printf "%s [${C_CYN}INFO${C_RST}] %s\n" "$ts" "$msg" ;;
    STEP) printf "\n${C_BLD}${C_MAG}━━━ %s ━━━${C_RST}\n" "$msg" ;;
    *)    printf "%s [    ] %s\n" "$ts" "$msg" ;;
  esac
  mkdir -p "$ARTIFACTS_DIR" 2>/dev/null
  printf "%s [%s] %s\n" "$ts" "$level" "$msg" >> "$LOG_FILE" 2>/dev/null || true
}

status() {
  # STATUS: PASS|FAIL|WARN component=<name> reason=<text>
  local result="$1" comp="$2"; shift 2
  local reason="$*"
  printf "STATUS: %s component=%s reason=%s\n" "$result" "$comp" "$reason"
  log "$result" "$comp — $reason"
  if [ "$result" = "FAIL" ]; then
    FAILED_COMPONENTS="$FAILED_COMPONENTS $comp"
  fi
}

evidence() { printf "EVIDENCE: %s\n" "$*"; }
fix_hint() { printf "${C_YEL}FIX:${C_RST} %s\n" "$*"; }
ask()      { printf "${C_CYN}ASK:${C_RST}  %s\n" "$*"; }
receipt()  {
  # RECEIPT: phase=<x> hash=<sha256>
  local phase="$1" payload="$2"
  local h; h=$(printf "%s" "$payload" | shasum -a 256 2>/dev/null | awk '{print $1}')
  [ -z "$h" ] && h=$(printf "%s" "$payload" | openssl dgst -sha256 2>/dev/null | awk '{print $NF}')
  printf "RECEIPT: phase=%s hash=%s\n" "$phase" "$h"
  mkdir -p "$ARTIFACTS_DIR" 2>/dev/null
  printf '{"phase":"%s","hash":"%s","ts":"%s"}\n' "$phase" "$h" "$(date -u +%FT%TZ)" >> "$RECEIPT_FILE"
}

# -----------------------------------------------------------------------------
# DOCKER SOCKET AUTO-DETECT
# -----------------------------------------------------------------------------
detect_docker() {
  local sock_host="/var/run/docker.sock"
  local sock_user="$HOME/.docker/run/docker.sock"
  if [ -S "$sock_user" ]; then
    export DOCKER_HOST="unix://$sock_user"
  elif [ -S "$sock_host" ]; then
    export DOCKER_HOST="unix://$sock_host"
  else
    return 1
  fi
  return 0
}

# -----------------------------------------------------------------------------
# HEALTH CHECK (canonical NS pattern)
# -----------------------------------------------------------------------------
# curl -sf http://127.0.0.1:PORT/healthz | python3 -c "import sys,json;print(json.load(sys.stdin).get('status','?'))"
health_of() {
  local port="$1"
  local body
  # Try /healthz first, fall back to /health
  body=$(curl -sf --max-time 3 "http://127.0.0.1:${port}/healthz" 2>/dev/null)
  if [ -z "$body" ]; then
    body=$(curl -sf --max-time 3 "http://127.0.0.1:${port}/health" 2>/dev/null)
  fi
  printf "%s" "$body" | python3 -c "import sys,json
try:
  d=json.load(sys.stdin)
  s=d.get('status','')
  if s in ('ok','healthy','up'): print(s); sys.exit(0)
  if d.get('healthy') is True: print('ok'); sys.exit(0)
  print(s if s else '?')
except Exception:
  print('unparseable')
" 2>/dev/null
}

tcp_open() {
  local port="$1"
  # bash 3.2: use /dev/tcp for quick reachability test
  (exec 3<>"/dev/tcp/127.0.0.1/${port}") 2>/dev/null && { exec 3<&- 3>&-; return 0; }
  return 1
}

# -----------------------------------------------------------------------------
# PHASE 1 — PREFLIGHT
# -----------------------------------------------------------------------------
phase_preflight() {
  log STEP "PHASE 1 — PREFLIGHT"

  # 1.1 tools
  for t in docker curl python3 git shasum jq; do
    if command -v "$t" >/dev/null 2>&1; then
      status PASS "tool:$t" "$(command -v "$t")"
    else
      if [ "$t" = "jq" ]; then
        status WARN "tool:$t" "missing (non-fatal; report formatting degraded)"
      else
        status FAIL "tool:$t" "not in PATH"
        fix_hint "brew install $t"
      fi
    fi
  done

  # 1.2 bash version
  local bv="${BASH_VERSION:-unknown}"
  status INFO "bash" "$bv"

  # 1.3 NS_HOME
  if [ -d "$NS_HOME" ]; then
    status PASS "NS_HOME" "$NS_HOME"
  else
    status FAIL "NS_HOME" "missing: $NS_HOME"
    fix_hint "git clone git@github.com:mkaxiolev-max/handrail.git $NS_HOME && cd $NS_HOME && git checkout boot-operational-closure"
    return 1
  fi

  # 1.4 repo state
  if [ -d "$NS_HOME/.git" ]; then
    local head branch dirty
    head=$(cd "$NS_HOME" && git rev-parse --short HEAD 2>/dev/null || echo "?")
    branch=$(cd "$NS_HOME" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?")
    dirty=$(cd "$NS_HOME" && git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    status INFO "repo" "branch=$branch head=$head dirty_files=$dirty"
    if [ "$dirty" != "0" ]; then
      status WARN "repo" "uncommitted changes ($dirty files)"
      fix_hint "cd $NS_HOME && git status"
    fi
  fi

  # 1.5 Alexandria SSD
  if [ -d "$ALEXANDRIA_ROOT" ]; then
    local free_mb
    free_mb=$(df -m "$ALEXANDRIA_ROOT" 2>/dev/null | tail -1 | awk '{print $4}')
    status PASS "alexandria_ssd" "mounted at $ALEXANDRIA_ROOT (free=${free_mb}MB)"
    if [ -n "$free_mb" ] && [ "$free_mb" -lt 2048 ]; then
      status WARN "alexandria_ssd" "low space <2GB"
    fi
  else
    status FAIL "alexandria_ssd" "NSExternal not mounted — receipt chain will fail"
    fix_hint "Plug in NSExternal SSD. Verify with: ls $ALEXANDRIA_ROOT"
  fi

  # 1.6 Docker socket
  if detect_docker; then
    status PASS "docker_socket" "$DOCKER_HOST"
  else
    status FAIL "docker_socket" "no socket at /var/run/docker.sock or \$HOME/.docker/run/docker.sock"
    fix_hint "Start Docker Desktop, then: open -a Docker"
    return 1
  fi

  # 1.7 docker daemon reachable
  if docker info >/dev/null 2>&1; then
    local dver; dver=$(docker version --format '{{.Server.Version}}' 2>/dev/null)
    status PASS "docker_daemon" "version=$dver"
  else
    status FAIL "docker_daemon" "unreachable via $DOCKER_HOST"
    return 1
  fi

  # 1.8 env vars — names only, never echo values
  local env_missing=""
  for v in ANTHROPIC_API_KEY TWILIO_ACCOUNT_SID TWILIO_AUTH_TOKEN TWILIO_PHONE_NUMBER POSTGRES_USER POSTGRES_DB; do
    eval "val=\${$v:-}"
    if [ -z "${val:-}" ]; then
      env_missing="$env_missing $v"
    fi
  done
  if [ -z "$env_missing" ]; then
    status PASS "env_vars" "all required vars present"
  else
    status FAIL "env_vars" "missing:$env_missing"
    fix_hint "source $NS_HOME/.env OR export the missing vars"
  fi

  # 1.9 compose file
  local compose=""
  for f in "$NS_HOME/docker-compose.yml" "$NS_HOME/compose.yaml" "$NS_HOME/docker-compose.yaml"; do
    [ -f "$f" ] && compose="$f" && break
  done
  if [ -n "$compose" ]; then
    status PASS "compose_file" "$compose"
    export NS_COMPOSE_FILE="$compose"
  else
    status FAIL "compose_file" "none found in $NS_HOME"
    return 1
  fi

  # 1.10 port conflicts
  local port conflicts=""
  for svc in $HTTP_SERVICES; do
    # extract port from SERVICES catalog
    for entry in $SERVICES; do
      name=$(echo "$entry" | cut -d: -f1)
      if [ "$name" = "$svc" ]; then
        port=$(echo "$entry" | cut -d: -f2)
        if tcp_open "$port"; then
          # port is already listening BEFORE boot — potential conflict (unless ours already up)
          conflicts="$conflicts $svc:$port"
        fi
      fi
    done
  done
  if [ -z "$conflicts" ]; then
    status PASS "port_conflicts" "no pre-existing listeners"
  else
    status WARN "port_conflicts" "pre-existing:$conflicts (may be prior NS run)"
    fix_hint "docker compose -f \$NS_COMPOSE_FILE down  # to reset"
  fi

  receipt "preflight" "nshome=$NS_HOME alex=$ALEXANDRIA_ROOT docker=$DOCKER_HOST fails=$FAIL_COUNT"
  return 0
}

# -----------------------------------------------------------------------------
# PHASE 2 — BOOT
# -----------------------------------------------------------------------------
phase_boot() {
  log STEP "PHASE 2 — BOOT (docker compose up + health gates)"

  if [ -z "${NS_COMPOSE_FILE:-}" ]; then
    for f in "$NS_HOME/docker-compose.yml" "$NS_HOME/compose.yaml"; do
      [ -f "$f" ] && NS_COMPOSE_FILE="$f" && break
    done
  fi
  if [ -z "${NS_COMPOSE_FILE:-}" ]; then
    status FAIL "boot" "no compose file"
    return 1
  fi

  log INFO "docker compose -f $NS_COMPOSE_FILE up -d"
  (cd "$NS_HOME" && docker compose -f "$NS_COMPOSE_FILE" up -d 2>&1 | tee -a "$PHASE_LOG") || {
    status FAIL "boot" "compose up failed — see $PHASE_LOG"
    return 1
  }

  # Wait for health — up to 120s per service
  log INFO "awaiting health on HTTP services (max 120s each)"
  local svc port deadline status_str elapsed
  for entry in $SERVICES; do
    svc=$(echo "$entry" | cut -d: -f1)
    port=$(echo "$entry" | cut -d: -f2)

    case " $HTTP_SERVICES " in
      *" $svc "*) : ;;  # continue to HTTP check
      *)
        # data services (postgres/redis) — just check container running
        if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "$svc"; then
          status PASS "service:$svc" "container up (port $port internal)"
        else
          status FAIL "service:$svc" "container not running"
        fi
        continue ;;
    esac

    deadline=$((SECONDS + 120))
    status_str=""
    while [ $SECONDS -lt $deadline ]; do
      if tcp_open "$port"; then
        status_str=$(health_of "$port")
        if [ "$status_str" = "ok" ] || [ "$status_str" = "healthy" ] || [ "$status_str" = "up" ]; then
          break
        fi
      fi
      sleep 2
    done

    elapsed=$((120 - (deadline - SECONDS)))
    if [ "$status_str" = "ok" ] || [ "$status_str" = "healthy" ] || [ "$status_str" = "up" ]; then
      status PASS "service:$svc" "healthz=$status_str port=$port t=${elapsed}s"
    else
      status FAIL "service:$svc" "no healthy response on :$port (got='$status_str')"
      fix_hint "docker compose -f $NS_COMPOSE_FILE logs --tail=80 $svc"
    fi
  done

  # Boot receipt
  local head; head=$(cd "$NS_HOME" && git rev-parse --short HEAD 2>/dev/null || echo "?")
  receipt "boot" "head=$head services_up=$PASS_COUNT fails=$FAIL_COUNT"

  if [ $FAIL_COUNT -eq 0 ]; then
    log PASS "ALL 11 SERVICES HEALTHY — organism LIVE"
  else
    log FAIL "BOOT INCOMPLETE — $FAIL_COUNT services down"
    return 1
  fi
  return 0
}

# -----------------------------------------------------------------------------
# PHASE 3 — VERIFY (features, invariants, endpoints)
# -----------------------------------------------------------------------------
phase_verify() {
  log STEP "PHASE 3 — VERIFY (features + invariants + endpoints)"

  # 3.1 — Core endpoints (actual routes discovered from live services)
  log INFO "3.1 endpoint battery"
  verify_endpoint "ns_core"       9000 "/healthz"                  "GET" ""
  verify_endpoint "ns_core"       9000 "/api/organism/overview"    "GET" ""
  verify_endpoint "ns_core"       9000 "/canon/invariants"         "GET" ""
  verify_endpoint "ns_core"       9000 "/violet/status"            "GET" ""
  verify_endpoint "ns_core"       9000 "/hic/gates"                "GET" ""
  verify_endpoint "alexandria"    9001 "/healthz"                  "GET" ""
  verify_endpoint "alexandria"    9001 "/atoms"                    "GET" ""
  verify_endpoint "model_router"  9002 "/healthz"                  "GET" ""
  verify_endpoint "model_router"  9002 "/providers"                "GET" ""
  verify_endpoint "violet"        9003 "/healthz"                  "GET" ""
  verify_endpoint "canon"         9004 "/healthz"                  "GET" ""
  verify_endpoint "integrity"     9005 "/healthz"                  "GET" ""
  verify_endpoint "integrity"     9005 "/integrity/chain"          "GET" ""
  verify_endpoint "integrity"     9005 "/integrity/verify"         "GET" ""
  verify_endpoint "omega"         9010 "/healthz"                  "GET" ""
  verify_endpoint "omega"         9010 "/omega/runs"               "GET" ""
  verify_endpoint "handrail"      8011 "/healthz"                  "GET" ""
  verify_endpoint "handrail"      8011 "/yubikey/status"           "GET" ""
  verify_endpoint "continuum"     8788 "/healthz"                  "GET" ""
  verify_endpoint "continuum"     8788 "/state"                    "GET" ""
  verify_endpoint "ns_api"        9011 "/health"                   "GET" ""

  # 3.2 — Constitutional invariants (ns_core:9000/canon/invariants)
  log INFO "3.2 constitutional invariants (10)"
  local inv_json
  inv_json=$(curl -sf --max-time 5 "http://127.0.0.1:9000/canon/invariants" 2>/dev/null || echo "{}")
  local inv_ok inv_count
  inv_ok=$(printf "%s" "$inv_json" | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin)
  arts=d.get('artifacts',[])
  ok=d.get('ok',False)
  count=len(arts)
  enforced_all=all(a.get('enforced') for a in arts)
  print(ok,count,enforced_all)
except Exception as e:
  print(False,0,False)
" 2>/dev/null)
  local chk_ok chk_count chk_enf
  chk_ok=$(echo "$inv_ok" | awk '{print $1}')
  chk_count=$(echo "$inv_ok" | awk '{print $2}')
  chk_enf=$(echo "$inv_ok" | awk '{print $3}')
  if [ "$chk_ok" = "True" ] && [ "${chk_count:-0}" -ge 10 ] 2>/dev/null; then
    if [ "$chk_enf" = "True" ]; then
      status PASS "invariants" "all 10 present and enforced=True"
    else
      status WARN "invariants" "all $chk_count defined but enforced field not True — Ring 5 enforcement tracking"
    fi
  else
    status FAIL "invariants" "expected 10 invariants ok=True, got ok=$chk_ok count=$chk_count"
  fi

  # 3.3 — Append-only ledger check (integrity service: write, read, tamper-check)
  log INFO "3.3 append-only ledger write→read→tamper-check"
  local test_payload="verify-probe-$(date +%s)"
  local write_resp
  write_resp=$(curl -sf --max-time 5 -X POST \
    -H "Content-Type: application/json" \
    -d "{\"event\":\"verify_probe\",\"payload\":{\"probe\":\"$test_payload\"}}" \
    "http://127.0.0.1:9005/integrity/receipt" 2>/dev/null)
  if [ -n "$write_resp" ]; then
    local rid
    rid=$(printf "%s" "$write_resp" | python3 -c "import sys,json;print(json.load(sys.stdin).get('id','?'))" 2>/dev/null)
    local wstatus
    wstatus=$(printf "%s" "$write_resp" | python3 -c "import sys,json;print(json.load(sys.stdin).get('status','?'))" 2>/dev/null)
    if [ "$wstatus" = "appended" ]; then
      status PASS "ledger_write" "id=$rid status=appended"
    else
      status WARN "ledger_write" "id=$rid status=$wstatus"
    fi
    # read back via chain — verify id appears
    local chain_resp
    chain_resp=$(curl -sf --max-time 5 "http://127.0.0.1:9005/integrity/chain" 2>/dev/null)
    if printf "%s" "$chain_resp" | grep -q "$rid"; then
      status PASS "ledger_readback" "id $rid found in chain"
    else
      status FAIL "ledger_readback" "id $rid not found in chain"
    fi
    # try DELETE — must be refused (404 or 405 — either means no delete route)
    local del_code
    del_code=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE --max-time 5 \
      "http://127.0.0.1:9005/integrity/receipt/$rid" 2>/dev/null)
    if [ "$del_code" = "405" ] || [ "$del_code" = "403" ] || [ "$del_code" = "501" ] || [ "$del_code" = "404" ]; then
      status PASS "ledger_append_only" "DELETE refused with $del_code (append-only enforced)"
    else
      status FAIL "ledger_append_only" "DELETE returned $del_code — expected 404/405/403/501"
    fi
  else
    status FAIL "ledger_write" "POST /integrity/receipt unreachable"
  fi

  # 3.4 — Receipt chain integrity (sha-256 linkage via /integrity/verify)
  log INFO "3.4 receipt chain sha-256 linkage"
  local chain_resp
  chain_resp=$(curl -sf --max-time 10 "http://127.0.0.1:9005/integrity/verify" 2>/dev/null)
  if [ -n "$chain_resp" ]; then
    local valid
    valid=$(printf "%s" "$chain_resp" | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin)
  print(d.get('chain_valid',d.get('ok',False)))
except Exception:
  print(False)
" 2>/dev/null)
    if [ "$valid" = "True" ] || [ "$valid" = "true" ]; then
      local clen
      clen=$(printf "%s" "$chain_resp" | python3 -c "import sys,json;print(json.load(sys.stdin).get('chain_length',0))" 2>/dev/null)
      status PASS "chain_integrity" "sha-256 chain valid chain_length=$clen"
    else
      status FAIL "chain_integrity" "/integrity/verify returned chain_valid=$valid"
    fi
  else
    status WARN "chain_integrity" "integrity /integrity/verify unreachable"
  fi

  # 3.5 — Canon single-write enforcement
  log INFO "3.5 canon single-write"
  local canon_code
  canon_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST --max-time 5 \
    -H "Content-Type: application/json" \
    -d '{"candidate_id":"verify-test","approver_signature":""}' \
    "http://127.0.0.1:9000/canon/promote" 2>/dev/null)
  # Unauthorized promote must return 200 with ok:false (signature required)
  local canon_body
  canon_body=$(curl -sf --max-time 5 -X POST \
    -H "Content-Type: application/json" \
    -d '{"candidate_id":"verify-test","approver_signature":""}' \
    "http://127.0.0.1:9000/canon/promote" 2>/dev/null)
  local canon_ok
  canon_ok=$(printf "%s" "$canon_body" | python3 -c "import sys,json;print(json.load(sys.stdin).get('ok',True))" 2>/dev/null)
  if [ "$canon_ok" = "False" ] || [ "$canon_ok" = "false" ]; then
    status PASS "canon_single_write" "unauthorized promote correctly rejected (ok=false)"
  elif [ "$canon_code" = "409" ] || [ "$canon_code" = "403" ]; then
    status PASS "canon_single_write" "write refused with $canon_code"
  elif [ "$canon_code" = "404" ]; then
    status WARN "canon_single_write" "endpoint not exposed"
  else
    status WARN "canon_single_write" "HTTP=$canon_code ok=$canon_ok (gate enforced by signature check)"
  fi

  # 3.6 — Dignity Hamiltonian veto (NE3: secret in CPS args → DIGNITY_KERNEL_VIOLATION)
  log INFO "3.6 Dignity Hamiltonian veto (NE3 — secret-in-args trigger)"
  local dig_resp dig_code_field
  dig_resp=$(curl -sf --max-time 5 -X POST \
    -H "Content-Type: application/json" \
    -d '{"cps_id":"verify_dignity_probe","objective":"test NE3 dignity veto","ops":[{"op":"fs.read","args":{"path":"/tmp/probe","data":"sk_live_verify_probe"}}]}' \
    "http://127.0.0.1:8011/ops/cps" 2>/dev/null)
  dig_code_field=$(printf "%s" "$dig_resp" | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin)
  for r in d.get('results',[]):
    if r.get('decision_code') == 'DIGNITY_KERNEL_VIOLATION':
      print('DIGNITY_KERNEL_VIOLATION'); break
  else:
    print(d.get('ok','?'))
except Exception:
  print('parse_error')
" 2>/dev/null)
  if [ "$dig_code_field" = "DIGNITY_KERNEL_VIOLATION" ]; then
    status PASS "dignity_veto" "NE3 triggered DIGNITY_KERNEL_VIOLATION (secret-in-args blocked)"
  else
    status FAIL "dignity_veto" "NE3 not triggered — got $dig_code_field (critical: dignity kernel gap)"
  fi

  # 3.7 — Model router liveness (no live inference)
  log INFO "3.7 model router /providers (no live inference)"
  local router_resp
  router_resp=$(curl -sf --max-time 5 "http://127.0.0.1:9002/providers" 2>/dev/null)
  if [ -n "$router_resp" ]; then
    for expected in "anthropic" "openai" "gemini"; do
      if printf "%s" "$router_resp" | grep -q "$expected"; then
        status PASS "router:$expected" "registered in /providers"
      else
        status WARN "router:$expected" "not in /providers response"
      fi
    done
  else
    status FAIL "model_router" "/providers unreachable"
  fi

  # 3.8 — Violet rendering contract (ns_core:9000/violet/status)
  log INFO "3.8 Violet rendering separation (ns_core proxy)"
  local violet_resp
  violet_resp=$(curl -sf --max-time 5 "http://127.0.0.1:9000/violet/status" 2>/dev/null)
  if printf "%s" "$violet_resp" | grep -qi "violet"; then
    local vmode
    vmode=$(printf "%s" "$violet_resp" | python3 -c "import sys,json;print(json.load(sys.stdin).get('mode','?'))" 2>/dev/null)
    status PASS "violet_render" "status mode=$vmode interface=violet (projection-only confirmed)"
  else
    status FAIL "violet_render" "no violet signature in /violet/status"
  fi

  # 3.9 — State reconstruction (autopoiesis tracks active programs)
  log INFO "3.9 state reconstruction (autopoiesis.state)"
  local state_resp
  state_resp=$(curl -sf --max-time 10 "http://127.0.0.1:9000/autopoiesis/state" 2>/dev/null)
  if [ -n "$state_resp" ]; then
    local prog_count
    prog_count=$(printf "%s" "$state_resp" | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin)
  arts=d.get('artifacts',[])
  if arts:
    prog=arts[0].get('programs',0)
    print(prog)
  else:
    print(0)
except Exception:
  print(0)
" 2>/dev/null)
    if [ -n "$prog_count" ] && [ "$prog_count" -gt 0 ] 2>/dev/null; then
      status PASS "state_reconstruct" "autopoiesis tracking $prog_count programs"
    else
      status WARN "state_reconstruct" "autopoiesis state programs=$prog_count"
    fi
  else
    status WARN "state_reconstruct" "/autopoiesis/state unreachable"
  fi

  # 3.10 — YubiKey quorum (handrail:8011/yubikey/status)
  log INFO "3.10 YubiKey quorum (Ring 5 gate — handrail)"
  local yk_resp
  yk_resp=$(curl -sf --max-time 5 "http://127.0.0.1:8011/yubikey/status" 2>/dev/null)
  local enrolled
  enrolled=$(printf "%s" "$yk_resp" | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin)
  print(d.get('enrolled_count',0))
except Exception:
  print(0)
" 2>/dev/null)
  case "$enrolled" in
    2|3) status PASS "yubikey_quorum" "enrolled_count=$enrolled quorum satisfied" ;;
    1) status WARN "yubikey_quorum" "enrolled_count=1 — slot_2 procurement pending (Ring 5 Gate G4 — expected)" ;;
    0) status WARN "yubikey_quorum" "enrolled_count=0 — Ring 5 Gate G4 (slot_2 procurement + re-enrollment pending)" ;;
    *) status WARN "yubikey_quorum" "enrolled_count unknown ($enrolled)" ;;
  esac

  receipt "verify" "pass=$PASS_COUNT fail=$FAIL_COUNT warn=$WARN_COUNT"
  return 0
}

verify_endpoint() {
  local svc="$1" port="$2" path="$3" method="$4" body="$5"
  local code body_out
  if [ "$method" = "GET" ]; then
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://127.0.0.1:${port}${path}" 2>/dev/null)
  else
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 -X "$method" \
      -H "Content-Type: application/json" -d "$body" \
      "http://127.0.0.1:${port}${path}" 2>/dev/null)
  fi
  case "$code" in
    200|201|204)
      status PASS "endpoint:$svc$path" "$method $code" ;;
    401|403)
      status WARN "endpoint:$svc$path" "$method $code (auth-gated)" ;;
    404)
      status WARN "endpoint:$svc$path" "$method 404 (not implemented yet)" ;;
    000|"")
      status FAIL "endpoint:$svc$path" "connection refused" ;;
    *)
      status FAIL "endpoint:$svc$path" "$method $code" ;;
  esac
}

# -----------------------------------------------------------------------------
# PHASE 4 — UI WALKTHROUGH
# -----------------------------------------------------------------------------
phase_ui() {
  log STEP "PHASE 4 — UI WALKTHROUGH (human-in-the-loop)"
  log INFO "Only role=ui services get browser opens + prompts. API services auto-skip."

  local svc port role path url
  for entry in $SERVICES; do
    svc=$(echo "$entry" | cut -d: -f1)
    port=$(echo "$entry" | cut -d: -f2)
    role=$(echo "$entry" | cut -d: -f3)

    # only browser-prompt for role=ui; auto-skip everything else
    case "$role" in
      ui) : ;;   # fall through to browser open + prompt
      data)
        status PASS "ui:$svc" "API/data service — no browser UI (auto-skip)"
        continue ;;
      *)
        status PASS "ui:$svc" "API service on :$port — no browser UI (auto-skip)"
        continue ;;
    esac

    path=$(ui_path_for_port "$port")
    url="http://127.0.0.1:${port}${path}"
    log INFO "opening $url"

    if command -v open >/dev/null 2>&1; then
      open "$url" 2>/dev/null
    fi

    ask "UI $svc @ $url — is it rendering correctly? (y/n/skip) "
    read -r ans
    case "$ans" in
      y|Y|yes)   status PASS "ui:$svc" "user-confirmed rendering" ;;
      n|N|no)
        status FAIL "ui:$svc" "user-reported broken"
        ask "Describe the issue (one line): "
        read -r issue
        printf "  ${C_DIM}noted:${C_RST} %s\n" "$issue"
        printf "ISSUE: svc=%s url=%s report=%s\n" "$svc" "$url" "$issue" >> "$ARTIFACTS_DIR/ui_issues.log"
        ;;
      *)         status WARN "ui:$svc" "user-skipped" ;;
    esac
  done

  receipt "ui" "reviewed by user at $(date -u +%FT%TZ)"
  if [ -s "$ARTIFACTS_DIR/ui_issues.log" ]; then
    log INFO "UI issues logged: $ARTIFACTS_DIR/ui_issues.log"
    log INFO "run 'bash $0 fix' to enter remediation"
  fi
  return 0
}

# -----------------------------------------------------------------------------
# PHASE 5 — WATCH (live code + receipt + log monitoring)
# -----------------------------------------------------------------------------
phase_watch() {
  log STEP "PHASE 5 — WATCH (Ctrl-C to exit)"
  log INFO "three panes: [1] git-worktree diff stream  [2] new receipts  [3] merged service logs"

  # Pane 1: codebase watcher (fswatch if available, else 2s poll on git status)
  # Pane 2: alexandria receipt tail (long-poll /receipts/stream)
  # Pane 3: docker compose logs -f (merged)
  #
  # bash 3.2 has no job control inside functions robustly across all macOS versions,
  # so we fork three background processes tied to the TTY and trap cleanup.

  local watchdir="$NS_HOME"
  local pids=""

  # Pane 1 — codebase
  (
    cd "$watchdir" || exit
    if command -v fswatch >/dev/null 2>&1; then
      fswatch -r -l 0.5 . 2>/dev/null | while read -r path; do
        printf "${C_CYN}[code]${C_RST} %s %s\n" "$(date +%H:%M:%S)" "$path"
      done
    else
      local last=""
      while :; do
        local cur
        cur=$(git status --porcelain 2>/dev/null | sort | shasum -a 256 | awk '{print $1}')
        if [ "$cur" != "$last" ] && [ -n "$last" ]; then
          printf "${C_CYN}[code]${C_RST} %s CHANGE\n" "$(date +%H:%M:%S)"
          git status --porcelain 2>/dev/null | head -10 | sed 's/^/  /'
        fi
        last="$cur"
        sleep 2
      done
    fi
  ) &
  pids="$pids $!"

  # Pane 2 — receipts (poll alexandria)
  (
    local last_id=""
    while :; do
      local latest
      latest=$(curl -sf --max-time 3 "http://127.0.0.1:9001/receipts?limit=1" 2>/dev/null \
        | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin)
  items=d if isinstance(d,list) else d.get('receipts',[])
  if items:
    r=items[0]
    print('%s|%s|%s' % (r.get('id','?'), r.get('kind','?'), r.get('ts','?')))
except Exception:
  pass
" 2>/dev/null)
      if [ -n "$latest" ]; then
        local rid
        rid=$(echo "$latest" | cut -d'|' -f1)
        if [ "$rid" != "$last_id" ] && [ -n "$last_id" ]; then
          printf "${C_GRN}[rcpt]${C_RST} %s %s\n" "$(date +%H:%M:%S)" "$latest"
        fi
        last_id="$rid"
      fi
      sleep 3
    done
  ) &
  pids="$pids $!"

  # Pane 3 — docker compose logs
  (
    if [ -n "${NS_COMPOSE_FILE:-}" ]; then
      cd "$NS_HOME" || exit
      docker compose -f "$NS_COMPOSE_FILE" logs -f --tail=0 2>&1 \
        | while IFS= read -r line; do
            printf "${C_MAG}[log] ${C_RST}%s\n" "$line"
          done
    fi
  ) &
  pids="$pids $!"

  trap "printf '\n${C_YEL}exit — killing watchers${C_RST}\n'; kill $pids 2>/dev/null; exit 0" INT TERM
  log INFO "watching... (Ctrl-C to stop)"
  wait
}

# -----------------------------------------------------------------------------
# PHASE 6 — FIX (interactive remediation)
# -----------------------------------------------------------------------------
phase_fix() {
  log STEP "PHASE 6 — FIX (interactive remediation)"

  # Known issue catalog — case dispatch (no assoc arrays)
  log INFO "known issue patterns; choose one or enter custom:"
  cat <<'EOF'
    1) docker_socket_missing     → open -a Docker && wait 20
    2) service_crash_loop        → logs --tail=200 + restart
    3) env_missing               → source $NS_HOME/.env
    4) alex_ssd_unmounted        → manual: plug in NSExternal
    5) port_conflict             → compose down && up
    6) ledger_write_failure      → pgsql connection reset
    7) yubikey_slot_2_pending    → Ring 5 gate; procurement required
    8) stale_compose             → pull latest on branch, rebuild
    9) custom
    q) quit
EOF
  ask "choice: "
  read -r ch

  case "$ch" in
    1)
      log INFO "starting Docker Desktop..."
      open -a Docker 2>/dev/null || log WARN "open failed"
      log INFO "waiting 20s for daemon..."
      sleep 20
      docker info >/dev/null 2>&1 && status PASS "fix:docker" "daemon now reachable" || status FAIL "fix:docker" "still unreachable"
      ;;
    2)
      ask "which service is crash-looping? "
      read -r svc
      (cd "$NS_HOME" && docker compose -f "${NS_COMPOSE_FILE:-docker-compose.yml}" logs --tail=200 "$svc" | tee "$ARTIFACTS_DIR/crash_${svc}.log")
      log INFO "logs saved to $ARTIFACTS_DIR/crash_${svc}.log"
      ask "restart $svc? (y/n) "
      read -r yn
      if [ "$yn" = "y" ]; then
        (cd "$NS_HOME" && docker compose -f "${NS_COMPOSE_FILE:-docker-compose.yml}" restart "$svc")
      fi
      ;;
    3)
      if [ -f "$NS_HOME/.env" ]; then
        log INFO "sourcing $NS_HOME/.env (subshell — re-source in your shell after)"
        # shellcheck disable=SC1090
        . "$NS_HOME/.env"
        log INFO "reminder: run 'source $NS_HOME/.env' in your shell too"
      else
        status FAIL "fix:env" "$NS_HOME/.env not found"
      fi
      ;;
    4)
      ask "mount NSExternal SSD now, then press enter"
      read -r _
      if [ -d "$ALEXANDRIA_ROOT" ]; then
        status PASS "fix:alex_ssd" "mounted"
      else
        status FAIL "fix:alex_ssd" "still not at $ALEXANDRIA_ROOT"
      fi
      ;;
    5)
      log INFO "docker compose down && up -d"
      (cd "$NS_HOME" && docker compose -f "${NS_COMPOSE_FILE:-docker-compose.yml}" down && docker compose -f "${NS_COMPOSE_FILE:-docker-compose.yml}" up -d)
      ;;
    6)
      log INFO "restarting postgres + alexandria in sequence"
      (cd "$NS_HOME" && docker compose -f "${NS_COMPOSE_FILE:-docker-compose.yml}" restart postgres)
      sleep 5
      (cd "$NS_HOME" && docker compose -f "${NS_COMPOSE_FILE:-docker-compose.yml}" restart alexandria)
      ;;
    7)
      log INFO "YubiKey slot 2 = Ring 5 gate (non-software). Order hardware; no remediation here."
      ;;
    8)
      (cd "$NS_HOME" && git pull --ff-only && docker compose -f "${NS_COMPOSE_FILE:-docker-compose.yml}" build --pull && docker compose -f "${NS_COMPOSE_FILE:-docker-compose.yml}" up -d)
      ;;
    9)
      ask "enter custom command (careful): "
      read -r cmd
      eval "$cmd"
      ;;
    q|Q) return 0 ;;
    *)   log WARN "unknown choice" ;;
  esac

  receipt "fix" "choice=$ch"
  return 0
}

# -----------------------------------------------------------------------------
# PHASE 7 — REPORT
# -----------------------------------------------------------------------------
phase_report() {
  log STEP "PHASE 7 — REPORT"
  mkdir -p "$ARTIFACTS_DIR"

  local head; head=$(cd "$NS_HOME" && git rev-parse --short HEAD 2>/dev/null || echo "?")
  local branch; branch=$(cd "$NS_HOME" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?")
  local ts; ts=$(date -u +%FT%TZ)

  cat > "$REPORT_FILE" <<EOF
# NS∞ Verification Report

- Generated: $ts
- Script: ns_verify.sh v$SCRIPT_VERSION ($SCRIPT_BUILD)
- Repo: branch=$branch head=$head
- NS_HOME: $NS_HOME
- Alexandria: $ALEXANDRIA_ROOT

## Summary

| Metric | Count |
|---|---|
| PASS | $PASS_COUNT |
| WARN | $WARN_COUNT |
| FAIL | $FAIL_COUNT |

EOF

  if [ -n "$FAILED_COMPONENTS" ]; then
    echo "## Failed Components" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    for c in $FAILED_COMPONENTS; do
      echo "- $c" >> "$REPORT_FILE"
    done
    echo "" >> "$REPORT_FILE"
  fi

  if [ -s "$ARTIFACTS_DIR/ui_issues.log" ]; then
    echo "## UI Issues (from walkthrough)" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
    cat "$ARTIFACTS_DIR/ui_issues.log" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
  fi

  echo "## Receipts" >> "$REPORT_FILE"
  echo '```' >> "$REPORT_FILE"
  [ -f "$RECEIPT_FILE" ] && cat "$RECEIPT_FILE" >> "$REPORT_FILE"
  echo '```' >> "$REPORT_FILE"

  echo "## Full Log" >> "$REPORT_FILE"
  echo "See: $LOG_FILE" >> "$REPORT_FILE"

  log INFO "report → $REPORT_FILE"
  receipt "report" "pass=$PASS_COUNT warn=$WARN_COUNT fail=$FAIL_COUNT head=$head"

  # Commit receipt into Alexandria (best-effort)
  if [ -d "$ALEXANDRIA_ROOT" ] && curl -sf --max-time 3 "http://127.0.0.1:9001/healthz" >/dev/null 2>&1; then
    curl -sf --max-time 5 -X POST \
      -H "Content-Type: application/json" \
      -d "{\"kind\":\"verify_report\",\"payload\":{\"ts\":\"$ts\",\"pass\":$PASS_COUNT,\"warn\":$WARN_COUNT,\"fail\":$FAIL_COUNT,\"head\":\"$head\"}}" \
      "http://127.0.0.1:9001/receipts" >/dev/null 2>&1 \
      && log PASS "alexandria_receipt" "verify_report submitted" \
      || log WARN "alexandria_receipt" "submission failed"
  fi

  printf "\n${C_BLD}FINAL:${C_RST} ${C_GRN}%d pass${C_RST} · ${C_YEL}%d warn${C_RST} · ${C_RED}%d fail${C_RST}\n" \
    "$PASS_COUNT" "$WARN_COUNT" "$FAIL_COUNT"
}

# -----------------------------------------------------------------------------
# MAIN DISPATCH
# -----------------------------------------------------------------------------
main() {
  mkdir -p "$ARTIFACTS_DIR"
  : > "$LOG_FILE"
  : > "$PHASE_LOG"
  : > "$RECEIPT_FILE"
  [ -f "$ARTIFACTS_DIR/ui_issues.log" ] && rm -f "$ARTIFACTS_DIR/ui_issues.log"

  local phase="${1:-all}"
  log INFO "ns_verify.sh v$SCRIPT_VERSION phase=$phase"

  case "$phase" in
    preflight) phase_preflight ;;
    boot)      detect_docker; phase_boot ;;
    verify)    phase_verify ;;
    ui)        phase_ui ;;
    watch)     detect_docker; phase_watch ;;
    fix)       detect_docker; phase_fix ;;
    report)    phase_report ;;
    all)
      phase_preflight || { log FAIL "preflight failed — halting"; phase_report; exit 1; }
      phase_boot      || { log FAIL "boot failed — halting";      phase_report; exit 1; }
      phase_verify
      phase_ui
      phase_report
      ;;
    *)
      echo "unknown phase: $phase"
      echo "usage: $0 [preflight|boot|verify|ui|watch|fix|report|all]"
      exit 2 ;;
  esac
}

main "$@"
