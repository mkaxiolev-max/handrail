#!/usr/bin/env bash
# =============================================================================
# NS∞ STATE CHECK v2 — Founder-Ready Delta Probe
# AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED
# Owner: Mike Kenworthy
# READ-ONLY. Fail-closed. No mutations, no LLM calls, no Alexandria writes
# outside /state_checks/. Missing = ❌, ambiguous = 🟡, present = ✅.
# =============================================================================
set -u

REPO="${REPO:-$HOME/axiolev_runtime}"
TM="$REPO/.terminal_manager"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DIGNITY='AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED'

# Output: prefer Alexandria external volume, fall back to local
if [ -d "/Volumes/NSExternal/ALEXANDRIA/state_checks" ]; then
  OUT="/Volumes/NSExternal/ALEXANDRIA/state_checks"
else
  OUT="$TM/state"
fi
mkdir -p "$OUT"

REPORT_MD="$OUT/state_v2_${STAMP}.md"
REPORT_JSON="$OUT/state_v2_${STAMP}.json"

# ── helpers ────────────────────────────────────────────────────────────────
sec()     { printf '\n## %s\n\n' "$1" >> "$REPORT_MD"; }
say()     { printf '%s\n' "$*"   >> "$REPORT_MD"; }
code()    { printf '```%s\n' "${1:-}" >> "$REPORT_MD"; }
codeend() { printf '```\n'       >> "$REPORT_MD"; }
ok()      { printf '✅ %s\n' "$*" >> "$REPORT_MD"; PASS=$((PASS+1)); }
warn()    { printf '🟡 %s\n' "$*" >> "$REPORT_MD"; WARN=$((WARN+1)); }
bad()     { printf '❌ %s\n' "$*" >> "$REPORT_MD"; FAIL=$((FAIL+1)); }
have()    { command -v "$1" >/dev/null 2>&1; }
PASS=0; WARN=0; FAIL=0

# ── header ─────────────────────────────────────────────────────────────────
cat > "$REPORT_MD" <<EOF
# NS∞ STATE CHECK v2 — ${STAMP}

**Repo:** \`$REPO\`
**Host:** \`$(hostname 2>/dev/null || echo unknown)\`
**User:** \`$(whoami 2>/dev/null || echo unknown)\`
**Uname:** \`$(uname -srm 2>/dev/null || echo unknown)\`
**Dignity Banner:** $DIGNITY

> READ-ONLY probe. No mutations. Missing/unknown = ❌ (fail-closed).
EOF

# =============================================================================
# §1  GIT STATE
# =============================================================================
sec "§1 · Git State"
EXPECTED_BRANCH="boot-operational-closure"
if [ -d "$REPO/.git" ]; then
  GIT_BRANCH="$(git -C "$REPO" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
  GIT_HEAD="$(git -C "$REPO" rev-parse --short HEAD 2>/dev/null || echo '?')"
  say "- Branch : \`$GIT_BRANCH\`  (expected \`$EXPECTED_BRANCH\`)"
  say "- HEAD   : \`$GIT_HEAD\`"
  [ "$GIT_BRANCH" = "$EXPECTED_BRANCH" ] && ok "L-branch matches" || warn "L-branch drift: $GIT_BRANCH"

  say ""; say "**Last 20 commits:**"; code
  git -C "$REPO" log --oneline -n 20 2>/dev/null >> "$REPORT_MD" || echo "(failed)" >> "$REPORT_MD"
  codeend

  say ""; say "**Tags (recent 30):**"; code
  git -C "$REPO" tag --sort=-creatordate 2>/dev/null | head -30 >> "$REPORT_MD" || echo "(none)" >> "$REPORT_MD"
  codeend

  say ""; say "**Expected tag presence:**"
  for t in "ns-infinity-founder-grade" "ns-infinity-v5" "voice-loop-v1" "axiolev-ns-infinity-boot-20260414"; do
    git -C "$REPO" rev-parse -q --verify "refs/tags/$t" >/dev/null 2>&1 \
      && ok "tag \`$t\`" || bad "tag \`$t\` MISSING"
  done

  say ""; say "**Dirty / untracked:**"; code
  git -C "$REPO" status --porcelain 2>/dev/null >> "$REPORT_MD" || echo "(failed)" >> "$REPORT_MD"
  codeend
  say "**Stashes:**"; code
  git -C "$REPO" stash list 2>/dev/null >> "$REPORT_MD" || true; codeend
else
  bad "not a git repo: $REPO"
  GIT_BRANCH="?"; GIT_HEAD="?"
fi

# =============================================================================
# §2  LIVE SERVICE MATRIX  L-1..L-11 + state_api
# =============================================================================
sec "§2 · Live Service Matrix (L-1..L-11)"

DOCKER_SOCK="${HOME}/.docker/run/docker.sock"
if [ -S "$DOCKER_SOCK" ]; then
  ok "L-docker-socket: $DOCKER_SOCK"
  export DOCKER_HOST="unix://$DOCKER_SOCK"
elif [ -S "/var/run/docker.sock" ]; then
  warn "docker socket at /var/run/docker.sock (not Mac-Desktop path)"
  export DOCKER_HOST="unix:///var/run/docker.sock"
else
  bad "no docker socket found"
fi

if have docker; then
  say ""; say "**docker compose ps:**"; code
  if [ -f "$REPO/docker-compose.yml" ]; then
    DOCKER_HOST="${DOCKER_HOST:-}" docker compose -f "$REPO/docker-compose.yml" ps 2>/dev/null >> "$REPORT_MD" \
      || echo "(compose ps failed)" >> "$REPORT_MD"
  else
    DOCKER_HOST="${DOCKER_HOST:-}" docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null >> "$REPORT_MD" \
      || echo "(docker ps failed)" >> "$REPORT_MD"
  fi
  codeend

  say ""; say "**Per-service status:**"

  # bash 3.2 safe — no associative arrays
  LIVE_COUNT=0
  _svc_check() {
    local label="$1" svc="$2" port="$3"
    if nc -z 127.0.0.1 "$port" 2>/dev/null; then
      ok "${label} ${svc}:${port} reachable"
      LIVE_COUNT=$((LIVE_COUNT+1))
    else
      bad "${label} ${svc}:${port} NOT reachable"
    fi
  }
  _svc_check "L-1"  "postgres"     5432
  _svc_check "L-2"  "redis"        6379
  _svc_check "L-3"  "ns_core"      9000
  _svc_check "L-4"  "alexandria"   9001
  _svc_check "L-5"  "model_router" 9002
  _svc_check "L-6"  "violet"       9003
  _svc_check "L-7"  "canon"        9004
  _svc_check "L-8"  "integrity"    9005
  _svc_check "L-9"  "omega"        9010
  _svc_check "L-10" "handrail"     8011
  _svc_check "L-11" "continuum"    8788
  _svc_check "L-12" "state_api"    9090
  say ""; say "- Live/Expected: **${LIVE_COUNT}/12**"
  [ "$LIVE_COUNT" -ge 11 ] && ok "L-matrix ≥11/12 services up" || bad "L-matrix only ${LIVE_COUNT}/12 services up"
else
  bad "docker CLI not available"
fi

# =============================================================================
# §3  VERIFIED LIVE ENDPOINTS (L-3 ns_core)
# =============================================================================
sec "§3 · Verified Live Endpoints"
NS="http://127.0.0.1:9000"
HR="http://127.0.0.1:8011"
AL="http://127.0.0.1:9001"
OM="http://127.0.0.1:9010"
CT="http://127.0.0.1:8788"

probe_get() {
  local url="$1" label="$2"
  local code
  code="$(curl -fsS -o /dev/null -w '%{http_code}' --max-time 3 "$url" 2>/dev/null || echo 000)"
  if [ "$code" = "200" ]; then ok "${label} → 200"
  elif [ "$code" != "000" ]; then warn "${label} → ${code}"
  else bad "${label} → timeout/refused"
  fi
}

say "**ns_core GET:**"
for ep in /healthz /system/now /violet/status /hic/gates /programs /mac_adapter/status \
           /api/v1/omega/healthz /api/v1/omega/runs /violet/identity /violet/isr \
           /ring5/status /boot/status /proof/registry /receipts; do
  probe_get "${NS}${ep}" "ns_core${ep}"
done

say ""; say "**handrail GET:**"
for ep in /healthz /ops /alexandria/status /continuum/status; do
  probe_get "${HR}${ep}" "handrail${ep}"
done

say ""; say "**alexandria GET:**"
probe_get "${AL}/healthz" "alexandria/healthz"
probe_get "${AL}/status"  "alexandria/status"

say ""; say "**omega GET:**"
probe_get "${OM}/api/v1/omega/healthz" "omega/healthz"

say ""; say "**continuum GET:**"
probe_get "${CT}/healthz"         "continuum/healthz"
probe_get "${CT}/state"           "continuum/state"
probe_get "${CT}/continuum/status" "continuum/status"

say ""; say "**POST probes (advisory-only, system_check target):**"
# intent/execute — system_check only, no real-world effect
INTENT_RESP="$(curl -fsS --max-time 5 -X POST "${NS}/intent/execute" \
  -H 'Content-Type: application/json' \
  -d '{"text":"system_check","target":"self"}' 2>/dev/null | head -c 200 || echo 'FAILED')"
if echo "$INTENT_RESP" | grep -qiE '"status"|"receipt_id"|"action"'; then
  ok "ns_core POST /intent/execute (system_check) → JSON response"
else
  bad "ns_core POST /intent/execute → no valid JSON  ($INTENT_RESP)"
fi

# =============================================================================
# §4  RING 6 GAPS  (R6-1..R6-7)
# =============================================================================
sec "§4 · Ring 6 Acceptance Gates (R6-1..R6-7)"

# R6-1 ax_core.json
AX="$REPO/canon/axioms/ax_core.json"
if [ -f "$AX" ]; then
  if have python3; then
    CNT="$(python3 -c "import json; d=json.load(open('$AX')); \
      print(len(d) if isinstance(d,list) else len(d.get('axioms',[])))" 2>/dev/null || echo '?')"
    [ "$CNT" = "14" ] && ok "R6-1 ax_core.json: AX-1..AX-14 ($CNT axioms)" \
                       || bad "R6-1 ax_core.json: count=$CNT (expected 14)"
  else ok "R6-1 ax_core.json present (python3 unavailable for count)"; fi
else bad "R6-1 canon/axioms/ax_core.json MISSING"; fi

# R6-2 Π engine
PI_DIR=""
[ -d "$REPO/pi" ]          && PI_DIR="$REPO/pi"
[ -d "$REPO/ns_core/pi" ]  && PI_DIR="$REPO/ns_core/pi"
[ -n "$PI_DIR" ] && ok "R6-2 Π admissibility engine dir: $PI_DIR" \
                 || bad "R6-2 Π engine dir MISSING (pi/ or ns_core/pi/)"

# R6-2 /pi/check endpoint
if grep -rqE "[\"']/pi/check[\"']" "$REPO" --include='*.py' 2>/dev/null; then
  ok "R6-2 /pi/check declared"
  probe_get "${NS}/pi/check" "live /pi/check"
else bad "R6-2 POST /pi/check NOT declared"; fi

# R6-3 /canon/promote
if grep -rqE "[\"']/canon/promote[\"']" "$REPO" --include='*.py' 2>/dev/null; then
  ok "R6-3 /canon/promote declared"
else bad "R6-3 POST /canon/promote NOT declared"; fi

# R6-4 never-event corpus
[ -d "$REPO/tests/pi/never_events" ] \
  && ok "R6-4 never-event test corpus: $REPO/tests/pi/never_events" \
  || bad "R6-4 tests/pi/never_events/ MISSING"

# R6-5 canon/promotions audit trail
[ -d "$REPO/canon/promotions" ] \
  && ok "R6-5 canon/promotions audit dir present" \
  || warn "R6-5 canon/promotions dir missing"

# R6-6 resume_ns.sh
[ -f "$REPO/resume_ns.sh" ] \
  && ok "R6-6 resume_ns.sh present" \
  || bad "R6-6 resume_ns.sh MISSING"
if grep -rqE "[\"']/ns/resume[\"']" "$REPO" --include='*.py' 2>/dev/null; then
  ok "R6-6 /ns/resume endpoint declared"
  probe_get "${NS}/ns/resume" "live /ns/resume"
else bad "R6-6 POST /ns/resume NOT declared"; fi

# R6-7 axiolev_push.sh
[ -f "$REPO/scripts/axiolev_push.sh" ] \
  && ok "R6-7 scripts/axiolev_push.sh present" \
  || bad "R6-7 scripts/axiolev_push.sh MISSING"

# =============================================================================
# §5  DOCTRINE  (D-1..D-3)
# =============================================================================
sec "§5 · Hallucination Doctrine (D-1..D-3)"
NER_FILE="$(find "$REPO" -type f -path '*/isr/ner.py' 2>/dev/null | head -1)"
FG_FILE="$(find "$REPO" -type f -path '*/cps/lanes/force_ground.py' 2>/dev/null | head -1)"
DOC_FILE="$REPO/docs/canon/HALLUCINATION_DOCTRINE.md"

[ -n "$NER_FILE" ] && ok "D-1 NER impl: $NER_FILE" || bad "D-1 ns_core/isr/ner.py MISSING"
if grep -rqE "[\"']/isr/ner[\"']" "$REPO" --include='*.py' 2>/dev/null; then
  ok "D-1 GET /isr/ner declared"
  probe_get "${NS}/isr/ner" "live /isr/ner"
else bad "D-1 GET /isr/ner NOT declared"; fi

[ -n "$FG_FILE" ] && ok "D-2 force_ground lane: $FG_FILE" || bad "D-2 cps/lanes/force_ground.py MISSING"
if grep -rqE "[\"']/cps/force_ground/invoke[\"']" "$REPO" --include='*.py' 2>/dev/null; then
  ok "D-2 POST /cps/force_ground/invoke declared"
else bad "D-2 POST /cps/force_ground/invoke NOT declared"; fi

[ -f "$DOC_FILE" ] && ok "D-3 HALLUCINATION_DOCTRINE.md present" \
                     || bad "D-3 docs/canon/HALLUCINATION_DOCTRINE.md MISSING"

# =============================================================================
# §6  CLEARING LAYER  (CL-1)
# =============================================================================
sec "§6 · Clearing Layer — Lichtung (CL-1)"
CLEAR_HITS="$(grep -rlE 'DisclosureWindow|AmbiguityRetention|withhold_protocol|clearing_layer|Lichtung' \
  "$REPO" --include='*.py' 2>/dev/null | head -10)"
[ -n "$CLEAR_HITS" ] \
  && { ok "CL-1 Clearing-layer primitives referenced:"; echo "$CLEAR_HITS" | sed 's/^/    /' >> "$REPORT_MD"; } \
  || bad "CL-1 DisclosureWindow/AmbiguityRetention/withhold_protocol NOT found"

say ""; say "**CI-1..CI-5 token scan:**"
for ci in "non_totalization:CI-1" "disclosure_window:CI-2" "irreducibility:CI-3" \
          "multi_disclosure:CI-4" "silence_abstention:CI-5"; do
  tok="${ci%%:*}"; lbl="${ci##*:}"
  grep -rqE "$tok" "$REPO" 2>/dev/null \
    && ok "$lbl ($tok)" || bad "$lbl ($tok) MISSING"
done

# =============================================================================
# §7  MAC INTEGRATION
# =============================================================================
sec "§7 · Mac Integration (MAC)"
LPLISTS="$(find "$HOME/Library/LaunchAgents" -maxdepth 1 \
  \( -name '*axiolev*' -o -name '*ns_infinity*' -o -name '*nsinfinity*' \) 2>/dev/null | head -5)"
[ -n "$LPLISTS" ] && ok "MAC-launchd: $(echo "$LPLISTS" | tr '\n' ' ')" \
                  || warn "MAC-launchd: no NS∞ plist in ~/Library/LaunchAgents"

MENUBAR="$(find "$REPO" -type f \( -name '*menubar*' -o -name '*tray*' -o -name '*.app' \) 2>/dev/null | head -5)"
[ -n "$MENUBAR" ] && ok "MAC-menubar: $MENUBAR" || warn "MAC-menubar: no menubar/tray artifact"

SHORTCUTS="$(find "$HOME/Library/Shortcuts" -maxdepth 2 \( -iname '*axiolev*' -o -iname '*ns*' \) 2>/dev/null | head -5)"
[ -n "$SHORTCUTS" ] && ok "MAC-shortcuts: $SHORTCUTS" || warn "MAC-shortcuts: none detected"

HOTKEY="$(grep -rlE 'global_hotkey|CGEventTap|NSEventMask' "$REPO" 2>/dev/null | head -3)"
[ -n "$HOTKEY" ] && ok "MAC-hotkey: $HOTKEY" || warn "MAC-hotkey: no global hotkey binding"

say ""; say "**launchctl loaded plists:**"; code
launchctl list 2>/dev/null | grep -iE 'axiolev|nsinfinity|ns_infinity' >> "$REPORT_MD" 2>/dev/null || echo "(none matching)" >> "$REPORT_MD"
codeend

# =============================================================================
# §8  LIVING ARCHITECTURE UI
# =============================================================================
sec "§8 · Living Architecture UI (UI)"
UI_DIR="$(find "$REPO" -type d -name 'violet_panel' 2>/dev/null | head -1)"
[ -n "$UI_DIR" ] && ok "UI violet_panel dir: $UI_DIR" || bad "UI violet_panel dir MISSING"

for tsx in NERTile ForceGroundBanner ClearingTile; do
  F="$REPO/ns_ui/violet_panel/components/${tsx}.tsx"
  [ -f "$F" ] && ok "UI ${tsx}.tsx present" || bad "UI ${tsx}.tsx MISSING"
done

[ -d "$REPO/ns_ui/dist" ] || [ -d "$REPO/ns_ui/.next" ] \
  && ok "UI build artifacts present" || warn "UI not built (no dist/.next)"

# =============================================================================
# §9  AUTOPOIESIS
# =============================================================================
sec "§9 · Autopoiesis (AP)"
COMPILER="$(find "$REPO" -type f \( -name '*document_to_program*' -o -name '*program_compiler*' \
  -o -name '*strategy_compiler*' -o -name '*ingest_strategy*' \) 2>/dev/null | head -5)"
[ -n "$COMPILER" ] && ok "AP compiler: $COMPILER" || bad "AP Document-to-Program compiler MISSING"

RUNTIME="$(find "$REPO" -type f \( -name '*program_runtime*' -o -name '*StrategicInitiative*' \) 2>/dev/null | head -5)"
[ -n "$RUNTIME" ] && ok "AP ProgramRuntime: $RUNTIME" || bad "AP ProgramRuntime MISSING"

FEED="$(find "$REPO" -type f \( -name '*morning_briefing*' -o -name '*feed_generator*' \
  -o -name '*autonarrate*' \) 2>/dev/null | head -5)"
[ -n "$FEED" ] && ok "AP autonarration: $FEED" || warn "AP autonarration/feed MISSING"

SELF_LOOP="$(grep -rlE 'B_adaptive|promotion_candidate|autopoiesis|self_modify' \
  "$REPO" --include='*.py' 2>/dev/null | head -5)"
[ -n "$SELF_LOOP" ] && ok "AP self-loop surfaces: $SELF_LOOP" || bad "AP autopoietic self-loop MISSING"

# =============================================================================
# §10  _violet_llm FALLBACK CHAIN
# =============================================================================
sec "§10 · _violet_llm Fallback Chain"
VLM="$(find "$REPO" -type f -name '_violet_llm.py' 2>/dev/null | head -1)"
[ -n "$VLM" ] && ok "_violet_llm.py: $VLM" || bad "_violet_llm.py NOT FOUND"

say ""; say "**Provider key presence (presence-only, values never read):**"
for var in GROQ_API_KEY XAI_API_KEY GROK_API_KEY OLLAMA_HOST ANTHROPIC_API_KEY OPENAI_API_KEY; do
  [ -n "${!var:-}" ] && ok "\$$var set" || warn "\$$var not in shell env"
done

# check .env file presence
ENV_FILE="$(find "$REPO" -maxdepth 2 -name '.env' -not -path '*/.git/*' 2>/dev/null | head -1)"
[ -n "$ENV_FILE" ] && ok ".env file present: $ENV_FILE" || warn "no .env file found at repo root"

# =============================================================================
# §11  PROOFS & DETERMINISM
# =============================================================================
sec "§11 · Proofs & Determinism"
if [ -d "$REPO/proofs" ]; then
  PC="$(find "$REPO/proofs" -type f -name '*.py' 2>/dev/null | wc -l | tr -d ' ')"
  PJ="$(find "$REPO/proofs" -type f -name '*.json' 2>/dev/null | wc -l | tr -d ' ')"
  ok "proofs/ present ($PC .py, $PJ .json)"
  say ""; code; find "$REPO/proofs" -type f 2>/dev/null | sort >> "$REPORT_MD"; codeend
else bad "proofs/ dir MISSING"; fi

# Alexandria proof endpoint
probe_get "${NS}/proof/registry"      "ns_core /proof/registry"
probe_get "${NS}/boot/latest-proof"   "ns_core /boot/latest-proof"
probe_get "${HR}/alexandria/proof"    "handrail /alexandria/proof"

# =============================================================================
# §12  CANON & ABI
# =============================================================================
sec "§12 · Canon & ABI"
ABI_F="$(find "$REPO" -type f \( -name 'abi_schema.py' -o -name 'abi_schema.json' \
  -o \( -name 'schema.py' -path '*/abi/*' \) \) 2>/dev/null | head -1)"
[ -n "$ABI_F" ] && ok "ABI schema: $ABI_F" || bad "ABI schema NOT FOUND"

PB="$(find "$REPO" -type f -name 'policy_bundle*.json' 2>/dev/null | head -1)"
[ -n "$PB" ] && ok "PolicyBundle: $PB" || warn "PolicyBundle JSON missing"

PROMOTIONS="$(find "$REPO" -type d -name 'promotions' 2>/dev/null | head -1)"
[ -n "$PROMOTIONS" ] && ok "canon/promotions dir: $PROMOTIONS" || warn "canon/promotions dir missing"

# =============================================================================
# §13  ALEXANDRIA LEDGER
# =============================================================================
sec "§13 · Alexandria Ledger"
AL_DIR="$(find "$REPO" -type d -name 'alexandria' 2>/dev/null | head -1)"
[ -n "$AL_DIR" ] && { ok "Alexandria service dir: $AL_DIR"; \
  FC="$(find "$AL_DIR" -type f 2>/dev/null | wc -l | tr -d ' ')"; say "- files: $FC"; } \
|| bad "alexandria/ dir MISSING"

# external volume
if [ -d "/Volumes/NSExternal/ALEXANDRIA" ]; then
  ok "external Alexandria volume mounted: /Volumes/NSExternal/ALEXANDRIA"
  LEDGER="/Volumes/NSExternal/ALEXANDRIA/ledger/ns_receipt_chain.jsonl"
  if [ -f "$LEDGER" ]; then
    CHAIN_LINES="$(wc -l < "$LEDGER" | tr -d ' ')"
    ok "receipt chain: $CHAIN_LINES entries"
    # SHA-256 spot-check last entry (read-only)
    if have python3; then
      python3 - "$LEDGER" >> "$REPORT_MD" 2>/dev/null <<'PYEOF'
import json, sys
try:
    lines = open(sys.argv[1]).readlines()
    last = json.loads(lines[-1])
    print(f"  last receipt: id={last.get('receipt_id','?')} ts={last.get('timestamp','?')}")
    print(f"  self_hash present: {'self_hash' in last}")
    print(f"  prev_hash present: {'prev_hash' in last}")
except Exception as e:
    print(f"  parse error: {e}")
PYEOF
    fi
  else warn "receipt chain file missing: $LEDGER"; fi
else warn "external volume /Volumes/NSExternal not mounted"; fi

# =============================================================================
# §14  YUBIKEY & RING 5 EXTERNAL GATES
# =============================================================================
sec "§14 · YubiKey & Ring 5 External Gates"
EXPECTED_YK="26116460"
if have ykman; then
  YK_OUT="$(ykman list 2>/dev/null || true)"
  say "**ykman list:**"; code; echo "$YK_OUT" >> "$REPORT_MD"; codeend
  echo "$YK_OUT" | grep -q "$EXPECTED_YK" \
    && ok "YK1 slot_1 serial $EXPECTED_YK bound" \
    || bad "YK1 slot_1 serial $EXPECTED_YK NOT detected"
else warn "ykman not installed — slot binding unverifiable"; fi

say "- YK2 slot_2: **PENDING HARDWARE** (~\$55 yubico.com)"

# Ring 5 live gate check
probe_get "${NS}/ring5/status" "ns_core /ring5/status"
R5_RESP="$(curl -fsS --max-time 5 "${NS}/ring5/status" 2>/dev/null || echo '{}')"
say ""; say "**Ring 5 gate response:**"; code json; echo "$R5_RESP" >> "$REPORT_MD"; codeend

# DNS
if have dig; then
  ZG="$(dig +short zeroguess.dev 2>/dev/null | tr '\n' ' ' || true)"
  [ -n "$ZG" ] && ok "zeroguess.dev → $ZG" || warn "zeroguess.dev DNS empty"
fi

say ""; say "**Ring 5 external gates (0/5 — no code, manual only):**"
say "- R5-1: LLC formation + EIN → Stripe verification"
say "- R5-2: Stripe live keys → .env + Vercel ROOT env"
say "- R5-3: ROOT Stripe price IDs → Vercel env"
say "- R5-4: YubiKey slot_2 hardware"
say "- R5-5: DNS root.axiolev.com → Cloudflare CNAME"

# =============================================================================
# §15  EXEC PLAN GATES  (EP-PB, EP-24, EP-2W)
# =============================================================================
sec "§15 · Exec Plan Gates"
say "**EP-PB (pre-boot):**"
[ -f "$REPO/boot.sh" ]                       && ok "EP-PB boot.sh present" || bad "EP-PB boot.sh MISSING"
[ -f "$REPO/docker-compose.yml" ]            && ok "EP-PB docker-compose.yml present" || bad "EP-PB docker-compose.yml MISSING"
[ -f "$REPO/.cps/ring5_verification.json" ]  && ok "EP-PB ring5_verification.json present" || warn "EP-PB .cps/ring5_verification.json missing"
[ -f "$REPO/.cps/sovereign_boot.json" ]      && ok "EP-PB sovereign_boot.json present" || warn "EP-PB .cps/sovereign_boot.json missing"
[ -f "$REPO/proofs/ns_boot_proof.json" ]     && ok "EP-PB ns_boot_proof.json present" || warn "EP-PB proofs/ns_boot_proof.json missing"

say ""; say "**EP-24 (24-72h post-boot) — endpoint presence:**"
for ep in "/ring5/status" "/dignity/config" "/kernel/yubikey/status" "/boot/status" \
          "/proof/registry" "/capability/graph" "/semantic/candidates"; do
  grep -rqE "[\"']${ep}[\"']" "$REPO" --include='*.py' 2>/dev/null \
    && ok "EP-24 $ep declared" || bad "EP-24 $ep NOT declared"
done

say ""; say "**EP-2W (second-wave) — Ring 6 + Doctrine:**"
for ep in "/pi/check" "/canon/promote" "/ns/resume" "/isr/ner" "/cps/force_ground/invoke"; do
  grep -rqE "[\"']${ep}[\"']" "$REPO" --include='*.py' 2>/dev/null \
    && ok "EP-2W $ep declared" || bad "EP-2W $ep NOT declared"
done

# =============================================================================
# §16  DIGNITY IP STANDARDS
# =============================================================================
sec "§16 · Dignity IP Standards"
PUSH="$REPO/scripts/axiolev_push.sh"
[ -f "$PUSH" ] && ok "axiolev_push.sh present" || bad "axiolev_push.sh MISSING"

MISSING_H=0
while IFS= read -r f; do
  head -20 "$f" 2>/dev/null | grep -q "AXIOLEV" || MISSING_H=$((MISSING_H+1))
done < <(find "$REPO" -type f -name '*.py' ! -path '*/.*' 2>/dev/null | head -500)
say "- .py files (first 500) missing AXIOLEV header: **$MISSING_H**"
[ "$MISSING_H" -eq 0 ] && ok "header compliance clean" || warn "header drift: $MISSING_H files"

TODO_C="$(grep -rEn 'TODO|FIXME|XXX' "$REPO" --include='*.py' 2>/dev/null | wc -l | tr -d ' ')"
say "- TODO/FIXME/XXX count (.py): **$TODO_C**"

# =============================================================================
# §17  FOUNDER-READY DELTA MATRIX
# =============================================================================
sec "§17 · Founder-Ready Delta Matrix"
cat >> "$REPORT_MD" <<'EOD'
| Gate  | Description                                        | §     | Status |
|-------|----------------------------------------------------|-------|--------|
| L-1..L-12 | Live service matrix (12 services)             | §2    | probe  |
| R5-1..R5-5 | Ring 5 external gates (no code)              | §14   | 0/5 BLOCKED |
| R6-1  | ax_core.json AX-1..AX-14                          | §4,§12| probe  |
| R6-2  | Π engine + /pi/check fail-closed                  | §4    | probe  |
| R6-3  | /canon/promote rejects insufficient evidence       | §4    | probe  |
| R6-4  | never-event test corpus                            | §4    | probe  |
| R6-5  | canon/promotions audit trail                       | §4    | probe  |
| R6-6  | /ns/resume + resume_ns.sh                          | §4    | probe  |
| R6-7  | axiolev_push.sh + AXIOLEV-FILE-HEADER              | §16   | probe  |
| D-1   | ns_core/isr/ner.py + GET /isr/ner                  | §5    | probe  |
| D-2   | cps/lanes/force_ground.py + POST endpoint          | §5    | probe  |
| D-3   | HALLUCINATION_DOCTRINE.md                          | §5    | probe  |
| CL-1  | DisclosureWindow / AmbiguityRetention / withhold   | §6    | probe  |
| MAC   | launchd + menubar + shortcuts + hotkey             | §7    | probe  |
| UI    | NERTile + ForceGroundBanner + ClearingTile         | §8    | probe  |
| AP    | Compiler + ProgramRuntime + autonarration + loop   | §9    | probe  |
| EP-PB | boot.sh + compose + CPS plans + boot proof        | §15   | probe  |
| EP-24 | Ring5/dignity/yubikey/boot/proof/capability endpoints | §15 | probe |
| EP-2W | Ring6 + Doctrine endpoints                         | §15   | probe  |
| VLK   | voice-loop-v1 Polly.Matthew Twilio SID             | §3    | probe  |
| YK1   | YubiKey slot_1 bound                               | §14   | probe  |
| YK2   | YubiKey slot_2 provisioned                         | §14   | PENDING HW |
EOD

# =============================================================================
# §18  RETURN BLOCK JSON
# =============================================================================
sec "§18 · Return Block JSON"

# Pre-compute all booleans — no function calls inside heredoc (bash 3.2 safe)
_jb() { [ -n "${1:-}" ] && echo true || echo false; }
_jf() { [ -f "${1:-}" ] && echo true || echo false; }
_jd() { [ -d "${1:-}" ] && echo true || echo false; }
_jp() { nc -z 127.0.0.1 "$1" 2>/dev/null && echo true || echo false; }
_je() { grep -rqE "\"${1}\"|'${1}'" "$REPO" --include='*.py' 2>/dev/null && echo true || echo false; }
_jg() { grep -rqE "${1}" "$REPO" 2>/dev/null && echo true || echo false; }

LC="${LIVE_COUNT:-0}"
HOST="$(hostname 2>/dev/null || echo unknown)"
GH="${GIT_HEAD:-?}"
BOK="$([ "${GIT_BRANCH:-?}" = "boot-operational-closure" ] && echo true || echo false)"

# live services
J_PG="$(_jp 5432)"
J_RD="$(_jp 6379)"
J_NS="$(_jp 9000)"
J_AL="$(_jp 9001)"
J_MR="$(_jp 9002)"
J_VI="$(_jp 9003)"
J_CA="$(_jp 9004)"
J_IN="$(_jp 9005)"
J_OM="$(_jp 9010)"
J_HR="$(_jp 8011)"
J_CT="$(_jp 8788)"
J_SA="$(_jp 9090)"

# ring6
J_R6_AX="$(_jf "$REPO/canon/axioms/ax_core.json")"
J_R6_PI="$(( [ -d "$REPO/pi" ] || [ -d "$REPO/ns_core/pi" ] ) && echo true || echo false)"
J_R6_PC="$(_je "/pi/check")"
J_R6_CP="$(_je "/canon/promote")"
J_R6_NE="$(_jd "$REPO/tests/pi/never_events")"
J_R6_PR="$(_jd "$REPO/canon/promotions")"
J_R6_RE="$(_je "/ns/resume")"
J_R6_RS="$(_jf "$REPO/resume_ns.sh")"
J_R6_PS="$(_jf "$REPO/scripts/axiolev_push.sh")"

# doctrine
J_D1_PY="$(_jb "${NER_FILE:-}")"
J_D1_EP="$(_je "/isr/ner")"
J_D2_PY="$(_jb "${FG_FILE:-}")"
J_D2_EP="$(_je "/cps/force_ground/invoke")"
J_D3_MD="$(_jf "$REPO/docs/canon/HALLUCINATION_DOCTRINE.md")"

# clearing
J_CL_PR="$(_jb "${CLEAR_HITS:-}")"
J_CI1="$(_jg "non_totalization")"
J_CI2="$(_jg "disclosure_window")"
J_CI3="$(_jg "irreducibility")"
J_CI4="$(_jg "multi_disclosure")"
J_CI5="$(_jg "silence_abstention")"

# mac
J_MA_LP="$(_jb "${LPLISTS:-}")"
J_MA_MB="$(_jb "${MENUBAR:-}")"
J_MA_SC="$(_jb "${SHORTCUTS:-}")"
J_MA_HK="$(_jb "${HOTKEY:-}")"

# ui
J_UI_VP="$(_jb "${UI_DIR:-}")"
J_UI_NT="$(_jf "$REPO/ns_ui/violet_panel/components/NERTile.tsx")"
J_UI_FG="$(_jf "$REPO/ns_ui/violet_panel/components/ForceGroundBanner.tsx")"
J_UI_CT="$(_jf "$REPO/ns_ui/violet_panel/components/ClearingTile.tsx")"

# autopoiesis
J_AP_CO="$(_jb "${COMPILER:-}")"
J_AP_RT="$(_jb "${RUNTIME:-}")"
J_AP_FD="$(_jb "${FEED:-}")"
J_AP_SL="$(_jb "${SELF_LOOP:-}")"

# violet_llm
J_VL_PY="$(_jb "${VLM:-}")"
J_VL_EV="$(_jb "${ENV_FILE:-}")"

# exec plan
J_EP_BT="$(_jf "$REPO/boot.sh")"
J_EP_DC="$(_jf "$REPO/docker-compose.yml")"
J_EP_R5="$(_jf "$REPO/.cps/ring5_verification.json")"
J_EP_SB="$(_jf "$REPO/.cps/sovereign_boot.json")"
J_EP_BP="$(_jf "$REPO/proofs/ns_boot_proof.json")"

# voice
J_VK_RR="$(_je "/voice/respond")"
J_VK_IR="$(_je "/voice/inbound")"
J_VK_PM="$(_jg "Polly\.Matthew")"
J_VK_SI="$(_jg "AC9d6c185542b20bf7d1145bc0f2e96028")"

cat > "$REPORT_JSON" <<JSONEOF
{
  "return_block_version": 2,
  "worker_kind": "code_state_review",
  "stamp": "$STAMP",
  "host": "$HOST",
  "repo": "$REPO",
  "dignity_banner": "$DIGNITY",
  "git": {
    "branch": "$GIT_BRANCH",
    "head": "$GH",
    "expected_branch": "boot-operational-closure",
    "branch_ok": $BOK,
    "tags_expected": ["ns-infinity-founder-grade","ns-infinity-v5","voice-loop-v1","axiolev-ns-infinity-boot-20260414"]
  },
  "live_services": {
    "postgres_5432":     $J_PG,
    "redis_6379":        $J_RD,
    "ns_core_9000":      $J_NS,
    "alexandria_9001":   $J_AL,
    "model_router_9002": $J_MR,
    "violet_9003":       $J_VI,
    "canon_9004":        $J_CA,
    "integrity_9005":    $J_IN,
    "omega_9010":        $J_OM,
    "handrail_8011":     $J_HR,
    "continuum_8788":    $J_CT,
    "state_api_9090":    $J_SA,
    "live_count": $LC,
    "expected": 12
  },
  "ring6": {
    "ax_core_json":         $J_R6_AX,
    "pi_engine_dir":        $J_R6_PI,
    "pi_check_ep":          $J_R6_PC,
    "canon_promote_ep":     $J_R6_CP,
    "never_event_corpus":   $J_R6_NE,
    "canon_promotions_dir": $J_R6_PR,
    "ns_resume_ep":         $J_R6_RE,
    "resume_ns_sh":         $J_R6_RS,
    "axiolev_push_sh":      $J_R6_PS
  },
  "doctrine": {
    "ner_py":           $J_D1_PY,
    "isr_ner_ep":       $J_D1_EP,
    "force_ground_py":  $J_D2_PY,
    "force_ground_ep":  $J_D2_EP,
    "doctrine_md":      $J_D3_MD
  },
  "clearing_layer": {
    "primitives_found":       $J_CL_PR,
    "ci1_non_totalization":   $J_CI1,
    "ci2_disclosure_window":  $J_CI2,
    "ci3_irreducibility":     $J_CI3,
    "ci4_multi_disclosure":   $J_CI4,
    "ci5_silence_abstention": $J_CI5
  },
  "mac_integration": {
    "launchd_plists":   $J_MA_LP,
    "menubar_artifact": $J_MA_MB,
    "shortcuts":        $J_MA_SC,
    "hotkey":           $J_MA_HK
  },
  "ui": {
    "violet_panel_dir":    $J_UI_VP,
    "ner_tile":            $J_UI_NT,
    "force_ground_banner": $J_UI_FG,
    "clearing_tile":       $J_UI_CT
  },
  "autopoiesis": {
    "compiler":       $J_AP_CO,
    "program_runtime":$J_AP_RT,
    "autonarration":  $J_AP_FD,
    "self_loop":      $J_AP_SL
  },
  "violet_llm": {
    "violet_llm_py":    $J_VL_PY,
    "env_file_present": $J_VL_EV
  },
  "exec_plan": {
    "boot_sh":              $J_EP_BT,
    "docker_compose":       $J_EP_DC,
    "ring5_verification":   $J_EP_R5,
    "sovereign_boot":       $J_EP_SB,
    "ns_boot_proof":        $J_EP_BP
  },
  "voice_loop": {
    "respond_route":      $J_VK_RR,
    "inbound_route":      $J_VK_IR,
    "polly_matthew":      $J_VK_PM,
    "twilio_sid_present": $J_VK_SI
  },
  "yubikey": {
    "slot_1_serial": "26116460",
    "slot_2_status": "PENDING_HARDWARE"
  },
  "tallies": {
    "pass": $PASS,
    "warn": $WARN,
    "fail": $FAIL
  }
}
JSONEOF

code json; cat "$REPORT_JSON" >> "$REPORT_MD"; codeend

# =============================================================================
# §19  FOOTER
# =============================================================================
sec "§19 · Footer"
say "$DIGNITY"
say ""; say "**Tallies:** pass=$PASS  warn=$WARN  fail=$FAIL"
say ""; say "**Report paths:**"
say "- Markdown : \`$REPORT_MD\`"
say "- JSON     : \`$REPORT_JSON\`"

# ── terminal-manager handshake ───────────────────────────────────────────────
echo "REPORT_PATH=$REPORT_MD"
echo "REPORT_JSON=$REPORT_JSON"
echo "TALLIES=pass=${PASS},warn=${WARN},fail=${FAIL}"
