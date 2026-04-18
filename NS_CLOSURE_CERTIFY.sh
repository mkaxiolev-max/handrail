#!/bin/bash

REPO="$HOME/axiolev_runtime"
ALEXANDRIA="/Volumes/NSExternal/ALEXANDRIA"
ARTIFACT_DIR="$REPO/artifacts"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
LOG="$REPO/closure_certify_${TIMESTAMP}.log"
PROOF_FILE="/tmp/ns_closure_proofs_${$}.jsonl"

if [ -d "$ALEXANDRIA" ]; then
  CERT_FILE="$ALEXANDRIA/CLOSURE_CERTIFICATION_${TIMESTAMP}.json"
else
  CERT_FILE="$ARTIFACT_DIR/CLOSURE_CERTIFICATION_${TIMESTAMP}.json"
fi

mkdir -p "$ARTIFACT_DIR"
: > "$LOG"
: > "$PROOF_FILE"

PASS=0
FAIL=0

G='\033[0;32m'
R='\033[0;31m'
Y='\033[1;33m'
C='\033[0;36m'
M='\033[0;35m'
NC='\033[0m'
BOLD='\033[1m'

log() {
  printf '%b\n' "$1" | tee -a "$LOG"
}

info() {
  log "${C}[INFO]${NC} $1"
}

pass() {
  PASS=$((PASS + 1))
  log "${G}[PASS]${NC} $1"
}

fail() {
  FAIL=$((FAIL + 1))
  log "${R}[FAIL]${NC} $1"
}

record_proof() {
  python3 - "$PROOF_FILE" "$1" "$2" "$3" <<'PY'
import json
import sys

path, status, check, detail = sys.argv[1:5]
with open(path, "a", encoding="utf-8") as handle:
    handle.write(json.dumps({
        "status": status,
        "check": check,
        "detail": detail,
    }, separators=(",", ":")) + "\n")
PY
}

check_ok() {
  local check_name="$1"
  local detail="$2"
  pass "$check_name - $detail"
  record_proof "PASS" "$check_name" "$detail"
}

check_fail() {
  local check_name="$1"
  local detail="$2"
  fail "$check_name - $detail"
  record_proof "FAIL" "$check_name" "$detail"
}

curl_json() {
  curl -sf --max-time 5 "$1" 2>/dev/null
}

json_get() {
  python3 - "$1" <<'PY'
import json
import sys

payload = sys.stdin.read()
key = sys.argv[1]
try:
    data = json.loads(payload)
except Exception:
    print("")
    raise SystemExit(0)

value = data
for part in key.split("."):
    if isinstance(value, dict):
        value = value.get(part)
    else:
        value = None
        break

if value is None:
    print("")
elif isinstance(value, (dict, list)):
    print(json.dumps(value))
else:
    print(value)
PY
}

header() {
  log ""
  log "${M}${BOLD}$1${NC}"
}

cd "$REPO" || exit 1
[ -f ".env" ] && { set -a; . ./.env; set +a; }

header "NS CLOSURE CERTIFY"
info "Repo: $REPO"
info "Log: $LOG"
info "Cert output: $CERT_FILE"

BRANCH="$(git branch --show-current 2>/dev/null || echo unknown)"
COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
info "Git: $BRANCH @ $COMMIT"

header "Runtime State"

STATE_JSON="$(curl_json http://127.0.0.1:9090/state || true)"
STATE_VALUE="$(printf '%s' "$STATE_JSON" | json_get state)"
BOOT_MODE="$(printf '%s' "$STATE_JSON" | json_get boot_mode)"
DEGRADED_JSON="$(printf '%s' "$STATE_JSON" | json_get degraded)"

if [ -n "$STATE_JSON" ]; then
  check_ok "state_api" "responding on :9090"
else
  check_fail "state_api" "not responding on :9090"
fi

if [ "$STATE_VALUE" = "LIVE" ]; then
  check_ok "state_value" "state=LIVE"
else
  check_fail "state_value" "state=${STATE_VALUE:-missing}"
fi

if [ "$BOOT_MODE" = "EXECUTION_ENABLED" ]; then
  check_ok "boot_mode" "boot_mode=EXECUTION_ENABLED"
else
  check_fail "boot_mode" "boot_mode=${BOOT_MODE:-missing}"
fi

if [ "$DEGRADED_JSON" = "[]" ]; then
  check_ok "degraded_services" "degraded=[]"
else
  check_fail "degraded_services" "degraded=${DEGRADED_JSON:-missing}"
fi

for pair in \
  "ns_core:http://127.0.0.1:9000/healthz" \
  "handrail:http://127.0.0.1:8011/healthz" \
  "continuum:http://127.0.0.1:8788/state" \
  "omega:http://127.0.0.1:9000/api/v1/omega/healthz" \
  "voice:http://127.0.0.1:9000/violet/status"; do
  NAME="${pair%%:*}"
  URL="${pair#*:}"
  if curl_json "$URL" >/dev/null; then
    check_ok "$NAME" "live at $URL"
  else
    check_fail "$NAME" "not responding at $URL"
  fi
done

header "Ollama"

if command -v ollama >/dev/null 2>&1; then
  OLLAMA_VERSION="$(ollama --version 2>/dev/null | head -1 || echo installed)"
  check_ok "ollama_binary" "$OLLAMA_VERSION"
else
  check_fail "ollama_binary" "ollama command not found"
fi

OLLAMA_TAGS="$(curl_json http://127.0.0.1:11434/api/tags || true)"
OLLAMA_MODEL_COUNT="$(printf '%s' "$OLLAMA_TAGS" | python3 - <<'PY'
import json
import sys
try:
    data = json.load(sys.stdin)
except Exception:
    print(0)
    raise SystemExit(0)
print(len(data.get("models", [])))
PY
)"

if [ -n "$OLLAMA_TAGS" ]; then
  check_ok "ollama_reachable" "local API reachable with ${OLLAMA_MODEL_COUNT} model(s)"
else
  check_fail "ollama_reachable" "local API not reachable on :11434"
fi

header "Organism UI"

if curl_json http://127.0.0.1:3000/organism >/dev/null; then
  check_ok "organism_ui" "frontend route responding at :3000/organism"
else
  check_fail "organism_ui" "frontend route not responding at :3000/organism"
fi

if curl_json http://127.0.0.1:9000/api/organism/overview >/dev/null; then
  check_ok "organism_backend" "overview endpoint responding at :9000/api/organism/overview"
else
  check_fail "organism_backend" "overview endpoint not responding at :9000/api/organism/overview"
fi

header "Proof Artifacts"

PROOF_MATCH="$(find "$ARTIFACT_DIR" "$ALEXANDRIA/receipts" -maxdepth 1 -type f 2>/dev/null | grep -E 'codex_e2e_proof|E2E_CLOSURE_PROOF|CODEX_E2E_PROOF' | tail -1 || true)"
if [ -n "$PROOF_MATCH" ]; then
  check_ok "e2e_proof" "found $PROOF_MATCH"
else
  check_fail "e2e_proof" "no codex end-to-end proof artifact found"
fi

header "Script Hygiene"

for script in NS_RIGHT_DEEP_VERIFY.sh NS_FINAL_CLOSURE_SPRINT.sh NS_CLOSURE_CERTIFY.sh; do
  if bash -n "$script" >/dev/null 2>&1; then
    check_ok "syntax:$script" "bash -n clean"
  else
    check_fail "syntax:$script" "bash -n failed"
  fi
done

header "Certification"

VERDICT="FOUNDER_READY"
if [ "$FAIL" -eq 0 ]; then
  VERDICT="BEYOND_FOUNDER_READY_FULLY_CLOSED"
elif [ "$PASS" -ge 10 ]; then
  VERDICT="LIVE_FOUNDER_PLUS"
fi

python3 - "$PROOF_FILE" "$CERT_FILE" "$VERDICT" "$COMMIT" "$BRANCH" "$PASS" "$FAIL" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

proof_file, cert_file, verdict, commit, branch, passed, failed = sys.argv[1:8]
proofs = []
with open(proof_file, "r", encoding="utf-8") as handle:
    for line in handle:
        line = line.strip()
        if not line:
            continue
        proofs.append(json.loads(line))

payload = {
    "document": "NS closure certification",
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "git_commit": commit,
    "git_branch": branch,
    "verdict": verdict,
    "passed_checks": int(passed),
    "failed_checks": int(failed),
    "ring_5_note": "Ring 5 remains deferred external work and is not treated as a software blocker.",
    "proofs": proofs,
}

out = Path(cert_file)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
PY

info "Passed: $PASS"
info "Failed: $FAIL"
info "Verdict: $VERDICT"
info "Certification: $CERT_FILE"

rm -f "$PROOF_FILE"
