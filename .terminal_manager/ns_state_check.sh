#!/usr/bin/env bash
# =============================================================================
# NS∞ STATE CHECK — Founder-Ready Delta Probe
# -----------------------------------------------------------------------------
# AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED
# Owner: Mike Kenworthy
# Purpose: READ-ONLY probe of the running NS∞ system on this Mac. Produces
#          the single authoritative state report that the terminal-manager
#          Claude (web chat) will parse to compute deltas against the
#          Founder-Ready acceptance criteria (Ring 6 AC-1..AC-7 + Doctrine
#          NER/force_ground + Clearing invariants + Mac integration + UI +
#          autopoesis).
#
# Invariants honored by this script:
#   - Dignity Kernel read-only    : no mutations anywhere
#   - Violet is projection        : we read /violet/* but never write
#   - Alexandria append-only      : we query ledger, never write
#   - LLMs never define truth     : no model calls, no _violet_llm invocation
#   - Fail-closed on ambiguity    : missing tool/endpoint → marked ❌ not ✅
#
# Run:  bash ~/axiolev_runtime/.terminal_manager/ns_state_check.sh
# Output: ~/axiolev_runtime/.terminal_manager/state/state_<UTC>.md (+ .json)
# =============================================================================

set -u  # deliberately NOT -e: we want the probe to continue on partial failure

REPO="${REPO:-$HOME/axiolev_runtime}"
TM="$REPO/.terminal_manager"
OUT="$TM/state"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
REPORT_MD="$OUT/state_${STAMP}.md"
REPORT_JSON="$OUT/state_${STAMP}.json"
DIGNITY='AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED'

# Expected anchors from Canon / prior sessions (the "ground truth" we diff against)
EXPECTED_BRANCH="boot-operational-closure"
EXPECTED_TAGS=(
  "ns-infinity-founder-grade"
  "ns-infinity-v5"
  "voice-loop-v1"
)
EXPECTED_TWILIO_SID="AC9d6c185542b20bf7d1145bc0f2e96028"
EXPECTED_TWILIO_NUMBER="+13072024418"
EXPECTED_DOCKER_SOCKET="unix:///Users/axiolevns/.docker/run/docker.sock"
EXPECTED_LLM_CHAIN=("Groq" "Grok" "Ollama" "Anthropic" "OpenAI" "canned")
EXPECTED_YUBIKEY_SLOT1="26116460"
EXPECTED_SERVICES_COUNT=7   # prior closure claim was 7/7 (some threads say 8/8 incl. router)
EXPECTED_PROOFS="10/10"
EXPECTED_DETERMINISM="1000/1000"
EXPECTED_ABI_FROZEN=12
EXPECTED_PROGRAMS=5
EXPECTED_RINGS=6            # Ring 6 = Layer 5.5 Constitutional wiring

mkdir -p "$OUT"

# -------- helpers -----------------------------------------------------------
sec() { printf '\n## %s\n\n' "$1" >> "$REPORT_MD"; }
say() { printf '%s\n' "$*" >> "$REPORT_MD"; }
code(){ printf '```%s\n' "${1:-}" >> "$REPORT_MD"; }
codeend(){ printf '```\n' >> "$REPORT_MD"; }
ok()   { printf '✅ %s\n' "$*" >> "$REPORT_MD"; }
warn() { printf '🟡 %s\n' "$*" >> "$REPORT_MD"; }
bad()  { printf '❌ %s\n' "$*" >> "$REPORT_MD"; }
have() { command -v "$1" >/dev/null 2>&1; }

# JSON accumulator (simple, line-based; compiled at the end)
JSON_TMP="$(mktemp)"
jrow() { printf '%s\n' "$1" >> "$JSON_TMP"; }

# -------- header ------------------------------------------------------------
cat > "$REPORT_MD" <<EOF
# NS∞ STATE CHECK — ${STAMP}

**Repo:** \`$REPO\`
**Host:** \`$(hostname 2>/dev/null || echo unknown)\`
**User:** \`$(whoami 2>/dev/null || echo unknown)\`
**Uname:** \`$(uname -a 2>/dev/null || echo unknown)\`
**Dignity Banner:** $DIGNITY

> READ-ONLY probe. No git mutation, no service restart, no LLM calls,
> no Alexandria writes. Missing/unknown = ❌ (fail-closed).
EOF

# =============================================================================
# 1. GIT STATE
# =============================================================================
sec "1 · Git State"
if [ -d "$REPO/.git" ]; then
  GIT_BRANCH="$(git -C "$REPO" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
  GIT_HEAD="$(git -C "$REPO" rev-parse --short HEAD 2>/dev/null || echo '?')"
  say "- Branch: \`$GIT_BRANCH\` (expected \`$EXPECTED_BRANCH\`)"
  say "- HEAD: \`$GIT_HEAD\`"
  [ "$GIT_BRANCH" = "$EXPECTED_BRANCH" ] && ok "branch matches" || warn "branch drift"

  say ""; say "**Last 20 commits:**"; code
  git -C "$REPO" log --oneline -n 20 2>/dev/null >> "$REPORT_MD" || echo "(git log failed)" >> "$REPORT_MD"
  codeend

  say ""; say "**Tags (recent 30):**"; code
  git -C "$REPO" tag --sort=-creatordate 2>/dev/null | head -30 >> "$REPORT_MD" || echo "(no tags)" >> "$REPORT_MD"
  codeend

  say ""; say "**Expected tag presence:**"
  for t in "${EXPECTED_TAGS[@]}"; do
    if git -C "$REPO" rev-parse -q --verify "refs/tags/$t" >/dev/null 2>&1; then
      ok "tag \`$t\` present"
    else
      bad "tag \`$t\` MISSING"
    fi
  done

  say ""; say "**Uncommitted changes:**"; code
  git -C "$REPO" status --porcelain 2>/dev/null >> "$REPORT_MD" || echo "(status failed)" >> "$REPORT_MD"
  codeend

  say "**Stashes:**"; code
  git -C "$REPO" stash list 2>/dev/null >> "$REPORT_MD" || true
  codeend

  say "**Remotes:**"; code
  git -C "$REPO" remote -v 2>/dev/null >> "$REPORT_MD" || true
  codeend
else
  bad "Repo not a git checkout at $REPO"
  GIT_BRANCH="?"; GIT_HEAD="?"
fi

# =============================================================================
# 2. RING 1–6 IMPLEMENTATION STATUS (Ring 6 = Constitutional wiring, Layer 5.5)
# =============================================================================
sec "2 · Rings 1–6 Implementation"
for r in 1 2 3 4 5 6; do
  found="$(find "$REPO" -type f \( -name "ring${r}*.py" -o -path "*/rings/${r}*" -o -path "*/ring_${r}*" \) 2>/dev/null | head -5)"
  if [ -n "$found" ]; then
    ok "Ring ${r}: files present"
    echo "$found" | sed 's/^/    /' >> "$REPORT_MD"
  else
    warn "Ring ${r}: no explicit ring-tagged files (may be distributed)"
  fi
done

# Ring 6 specific: Canon axioms, Π admissibility engine, promotion endpoint
say ""; say "**Ring 6 acceptance anchors:**"
[ -f "$REPO/canon/axioms/ax_core.json" ] && ok "AC-1 \`canon/axioms/ax_core.json\` present" || bad "AC-1 \`canon/axioms/ax_core.json\` MISSING"
[ -d "$REPO/pi" ] || [ -d "$REPO/ns_core/pi" ] && ok "Π admissibility engine dir present" || bad "Π engine dir MISSING"
[ -d "$REPO/tests/pi/never_events" ] && ok "AC-2 never-event test corpus present" || bad "AC-2 never-event test corpus MISSING"
[ -d "$REPO/canon/promotions" ] && ok "promotion audit trail dir present" || warn "promotion trail dir missing"
[ -f "$REPO/resume_ns.sh" ] && ok "AC-6 \`resume_ns.sh\` present" || bad "AC-6 \`resume_ns.sh\` MISSING"
[ -f "$REPO/scripts/axiolev_push.sh" ] && ok "AC-7 \`axiolev_push.sh\` present" || bad "AC-7 \`axiolev_push.sh\` MISSING"

# =============================================================================
# 3. DOCKER / SERVICES HEALTH
# =============================================================================
sec "3 · Services (Docker)"
say "- Expected Docker socket: \`$EXPECTED_DOCKER_SOCKET\`"
if [ -S "${EXPECTED_DOCKER_SOCKET#unix://}" ]; then
  ok "Mac Docker socket present at expected path"
elif [ -S "/var/run/docker.sock" ]; then
  warn "socket found at default /var/run/docker.sock (not Mac desktop path)"
else
  bad "no docker socket at expected or default path"
fi

if have docker; then
  say ""; say "**docker compose ps:**"; code
  if [ -f "$REPO/docker-compose.yml" ]; then
    docker compose -f "$REPO/docker-compose.yml" ps 2>>"$REPORT_MD" >> "$REPORT_MD" || echo "(compose ps failed)" >> "$REPORT_MD"
  else
    docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>>"$REPORT_MD" >> "$REPORT_MD" || echo "(docker ps failed)" >> "$REPORT_MD"
  fi
  codeend

  HEALTHY_COUNT="$(docker ps --filter 'health=healthy' --format '{{.Names}}' 2>/dev/null | wc -l | tr -d ' ' || echo 0)"
  TOTAL_COUNT="$(docker ps --format '{{.Names}}' 2>/dev/null | wc -l | tr -d ' ' || echo 0)"
  say ""; say "- Healthy/Total: **${HEALTHY_COUNT}/${TOTAL_COUNT}** (expected ≥ $EXPECTED_SERVICES_COUNT healthy)"
  if [ "${HEALTHY_COUNT:-0}" -ge "$EXPECTED_SERVICES_COUNT" ]; then
    ok "services healthy count meets expectation"
  else
    bad "services healthy count below expectation"
  fi
else
  bad "\`docker\` CLI not available"
  HEALTHY_COUNT=0; TOTAL_COUNT=0
fi

# =============================================================================
# 4. ENDPOINT INVENTORY (static grep of FastAPI decorators)
# =============================================================================
sec "4 · Endpoint Inventory"
if have grep; then
  say "**Declared routes (grep):**"; code
  grep -RhnE '@(router|app)\.(get|post|put|delete|patch)\(' "$REPO" --include='*.py' 2>/dev/null \
    | sed -E 's/.*@(router|app)\.(get|post|put|delete|patch)\(["'"'"']([^"'"'"']+).*/\2 \3/' \
    | sort -u | head -200 >> "$REPORT_MD" || true
  codeend
fi

say ""; say "**Expected Ring 6 / Doctrine / Voice endpoints:**"
CRITICAL_ENDPOINTS=(
  "/pi/check"
  "/canon/promote"
  "/ns/resume"
  "/isr/ner"
  "/cps/force_ground/invoke"
  "/voice/respond"
  "/violet/identity"
  "/violet/status"
)
for ep in "${CRITICAL_ENDPOINTS[@]}"; do
  if grep -rqE "[\"']${ep}[\"']" "$REPO" --include='*.py' 2>/dev/null; then
    ok "endpoint \`$ep\` declared"
  else
    bad "endpoint \`$ep\` NOT declared"
  fi
done

# Live probe of localhost endpoints (best-effort)
say ""; say "**Live endpoint probes (localhost):**"
PORTS=(8000 8080 9000 9001 9002)
for port in "${PORTS[@]}"; do
  for path in /healthz /health /isr/ner /violet/identity; do
    code_http="$(curl -fsS -o /dev/null -w '%{http_code}' --max-time 2 "http://127.0.0.1:${port}${path}" 2>/dev/null || echo 000)"
    if [ "$code_http" = "200" ]; then
      ok ":${port}${path} → 200"
    fi
  done
done

# =============================================================================
# 5. PROOFS (10/10) and DETERMINISM (1000/1000)
# =============================================================================
sec "5 · Proofs & Determinism"
if [ -d "$REPO/proofs" ]; then
  PROOF_COUNT="$(find "$REPO/proofs" -type f -name '*.py' 2>/dev/null | wc -l | tr -d ' ')"
  ok "proofs/ present ($PROOF_COUNT .py files)"
  say ""; say "**Proof files:**"; code
  find "$REPO/proofs" -type f -name '*.py' 2>/dev/null | sort >> "$REPORT_MD"
  codeend
else
  bad "no \`proofs/\` directory (expected $EXPECTED_PROOFS)"
  PROOF_COUNT=0
fi

# Look for last proof-run receipts (read-only; do NOT re-run)
say ""; say "**Last proof/determinism receipts in Alexandria (if reachable):**"; code
for port in 8000 8080 9000; do
  for path in "/isr/proofs/last" "/alexandria/receipts?kind=PROOF_RUN&limit=1" "/alexandria/receipts?kind=DETERMINISM&limit=1"; do
    out="$(curl -fsS --max-time 2 "http://127.0.0.1:${port}${path}" 2>/dev/null || true)"
    [ -n "$out" ] && echo "${port}${path}: $out" >> "$REPORT_MD"
  done
done
codeend

# =============================================================================
# 6. _violet_llm FALLBACK CHAIN (provider presence only, never values)
# =============================================================================
sec "6 · _violet_llm Fallback Chain"
say "Expected order: ${EXPECTED_LLM_CHAIN[*]}"
VIOLET_LLM_FILE="$(find "$REPO" -type f -name '_violet_llm.py' 2>/dev/null | head -1)"
if [ -n "$VIOLET_LLM_FILE" ]; then
  ok "\`_violet_llm.py\` found: $VIOLET_LLM_FILE"
else
  bad "\`_violet_llm.py\` not found"
fi

# Env key PRESENCE (never value)
say ""; say "**Provider key presence (presence only, values never read):**"
for var in GROQ_API_KEY XAI_API_KEY GROK_API_KEY OLLAMA_HOST ANTHROPIC_API_KEY OPENAI_API_KEY; do
  if [ -n "${!var:-}" ]; then ok "\$$var set"; else warn "\$$var not set in current shell"; fi
done

# =============================================================================
# 7. CANON & ABI (12 frozen objects)
# =============================================================================
sec "7 · Canon & ABI"
if [ -f "$REPO/canon/axioms/ax_core.json" ]; then
  if have python3; then
    AXIOM_COUNT="$(python3 -c "import json; d=json.load(open('$REPO/canon/axioms/ax_core.json')); print(len(d) if isinstance(d,list) else len(d.get('axioms',[])))" 2>/dev/null || echo '?')"
    say "- ax_core.json axiom count: **$AXIOM_COUNT** (expected 14)"
    [ "$AXIOM_COUNT" = "14" ] && ok "AX-1..AX-14 present" || bad "axiom count mismatch"
  fi
else
  bad "ax_core.json missing"
fi

ABI_FILE="$(find "$REPO" -type f \( -name 'abi_schema.py' -o -name 'schema.py' -path '*/abi/*' -o -name 'abi_schema.json' \) 2>/dev/null | head -1)"
if [ -n "$ABI_FILE" ]; then
  ok "ABI schema file: $ABI_FILE"
else
  bad "ABI schema file not found (expected $EXPECTED_ABI_FROZEN frozen objects)"
fi

# Policy bundle
POLICY_BUNDLE="$(find "$REPO" -type f -name 'policy_bundle*.json' 2>/dev/null | head -1)"
[ -n "$POLICY_BUNDLE" ] && ok "PolicyBundle found: $POLICY_BUNDLE" || warn "no PolicyBundle json found"

# =============================================================================
# 8. ALEXANDRIA LEDGER
# =============================================================================
sec "8 · Alexandria Ledger"
ALEX_DIR="$(find "$REPO" -type d -name 'alexandria' 2>/dev/null | head -1)"
if [ -n "$ALEX_DIR" ]; then
  ok "Alexandria dir: $ALEX_DIR"
  LEDGER_FILES="$(find "$ALEX_DIR" -type f 2>/dev/null | wc -l | tr -d ' ')"
  say "- Ledger files present: $LEDGER_FILES"
else
  bad "no alexandria/ directory found"
fi

# =============================================================================
# 9. YUBIKEY & SECURITY GATES
# =============================================================================
sec "9 · YubiKey & Ring 5 External Gates"
if have ykman; then
  YK_INFO="$(ykman list 2>/dev/null || true)"
  say "**ykman list:**"; code; echo "$YK_INFO" >> "$REPORT_MD"; codeend
  if echo "$YK_INFO" | grep -q "$EXPECTED_YUBIKEY_SLOT1"; then
    ok "YubiKey slot_1 ($EXPECTED_YUBIKEY_SLOT1) bound"
  else
    bad "YubiKey slot_1 ($EXPECTED_YUBIKEY_SLOT1) NOT detected"
  fi
else
  warn "\`ykman\` CLI not installed — slot binding unverifiable from shell"
fi
say "- slot_2: **PENDING HARDWARE** (~\$55 yubico.com) — force_ground abort + G5 ratification are fail-closed until provisioned."

# DNS for zeroguess.dev
if have dig; then
  ZG_DNS="$(dig +short zeroguess.dev 2>/dev/null || true)"
  [ -n "$ZG_DNS" ] && ok "zeroguess.dev resolves: $ZG_DNS" || warn "zeroguess.dev DNS empty"
fi

# =============================================================================
# 10. VOICE LOOP (Twilio)
# =============================================================================
sec "10 · Voice Loop"
say "- Expected SID: \`$EXPECTED_TWILIO_SID\`"
say "- Expected number: \`$EXPECTED_TWILIO_NUMBER\`"
if grep -rqE "AC9d6c185542b20bf7d1145bc0f2e96028|3072024418" "$REPO" 2>/dev/null; then
  ok "Twilio SID / number referenced in repo"
else
  warn "Twilio identifiers not found in repo (may be env-only)"
fi
if grep -rqE "Polly\.Matthew" "$REPO" 2>/dev/null; then
  ok "Polly.Matthew voice configured"
else
  bad "Polly.Matthew not configured"
fi
if grep -rqE "/voice/respond" "$REPO" --include='*.py' 2>/dev/null; then
  ok "/voice/respond route present"
else
  bad "/voice/respond route MISSING"
fi

# =============================================================================
# 11. DOCTRINE (NER + force_ground) — Hallucination Doctrine readiness
# =============================================================================
sec "11 · Hallucination Doctrine (NER + force_ground)"
NER_FILE="$(find "$REPO" -type f -path '*/isr/ner.py' 2>/dev/null | head -1)"
FG_FILE="$(find "$REPO" -type f -path '*/cps/lanes/force_ground.py' 2>/dev/null | head -1)"
DOC_FILE="$REPO/docs/canon/HALLUCINATION_DOCTRINE.md"
[ -n "$NER_FILE" ] && ok "NER impl: $NER_FILE" || bad "NER impl MISSING (Packet 02 not landed)"
[ -n "$FG_FILE" ] && ok "force_ground lane: $FG_FILE" || bad "force_ground lane MISSING (Packet 03 not landed)"
[ -f "$DOC_FILE" ] && ok "HALLUCINATION_DOCTRINE.md present" || bad "HALLUCINATION_DOCTRINE.md MISSING (Packet 04 not landed)"

# =============================================================================
# 12. CLEARING LAYER (Lichtung — Disclosure/Ambiguity/Abstention)
# =============================================================================
sec "12 · Clearing Layer (Lichtung)"
CLEAR_HITS="$(grep -rlE 'DisclosureWindow|AmbiguityRetention|withhold_protocol|clearing_layer|Lichtung' "$REPO" --include='*.py' 2>/dev/null | head -10)"
if [ -n "$CLEAR_HITS" ]; then
  ok "Clearing-layer primitives referenced:"
  echo "$CLEAR_HITS" | sed 's/^/    /' >> "$REPORT_MD"
else
  bad "Clearing Layer primitives (Disclosure Window / Ambiguity Retention / Abstention) NOT found"
fi

# Invariants checklist (static presence of canonical tokens)
say ""; say "**Canonical Invariants (CI-1..CI-5):**"
for ci in "non_totalization:CI-1" "disclosure_window:CI-2" "irreducibility:CI-3" "multi_disclosure:CI-4" "silence_abstention:CI-5"; do
  token="${ci%%:*}"; label="${ci##*:}"
  if grep -rqE "$token" "$REPO" 2>/dev/null; then ok "$label ($token) referenced"; else bad "$label ($token) MISSING"; fi
done

# =============================================================================
# 13. MAC INTEGRATION (launchd, menubar, shortcuts, native surfaces)
# =============================================================================
sec "13 · Mac Integration"
# launchd plist
LAUNCH_PLIST="$(find "$HOME/Library/LaunchAgents" -maxdepth 1 -name '*axiolev*' -o -name '*ns_infinity*' -o -name '*nsinfinity*' 2>/dev/null | head -3)"
[ -n "$LAUNCH_PLIST" ] && ok "launchd plist(s): $LAUNCH_PLIST" || warn "no launchd plist for NS∞ found in ~/Library/LaunchAgents"

# Menubar / tray app
MENUBAR_HIT="$(find "$REPO" -type f \( -name '*menubar*' -o -name '*tray*' -o -name '*.app' \) 2>/dev/null | head -5)"
[ -n "$MENUBAR_HIT" ] && ok "menubar/tray artifacts present" || warn "no menubar/tray app found"

# Shortcuts / URL handler
SHORTCUT_HIT="$(find "$HOME/Library/Shortcuts" -maxdepth 2 -iname '*axiolev*' -o -iname '*ns∞*' 2>/dev/null | head -5)"
[ -n "$SHORTCUT_HIT" ] && ok "Mac Shortcuts present" || warn "no Axiolev Mac Shortcuts detected"

# Hot-key / global binding
HOTKEY_HIT="$(grep -rlE 'global_hotkey|CGEventTap|NSEventMask' "$REPO" 2>/dev/null | head -3)"
[ -n "$HOTKEY_HIT" ] && ok "global hotkey surface referenced" || warn "no global hotkey binding found"

# =============================================================================
# 14. LIVING ARCHITECTURE UI (VioletPanel + NER tile + ForceGround banner)
# =============================================================================
sec "14 · Living Architecture UI"
UI_DIR="$(find "$REPO" -type d -name 'violet_panel' 2>/dev/null | head -1)"
[ -n "$UI_DIR" ] && ok "violet_panel dir: $UI_DIR" || bad "violet_panel UI dir MISSING"
[ -f "$REPO/ns_ui/violet_panel/components/NERTile.tsx" ] && ok "NERTile.tsx present" || bad "NERTile.tsx MISSING"
[ -f "$REPO/ns_ui/violet_panel/components/ForceGroundBanner.tsx" ] && ok "ForceGroundBanner.tsx present" || bad "ForceGroundBanner.tsx MISSING"
[ -f "$REPO/ns_ui/violet_panel/components/ClearingTile.tsx" ] && ok "ClearingTile.tsx (disclosure+ambiguity+abstention)" || bad "ClearingTile.tsx MISSING"

# Frontend build artifacts
[ -d "$REPO/ns_ui/dist" ] || [ -d "$REPO/ns_ui/.next" ] && ok "UI build artifacts present" || warn "UI not built"

# =============================================================================
# 15. AUTOPOIESIS (self-production loops: strategy→program compiler + feedback)
# =============================================================================
sec "15 · Autopoiesis"
COMPILER_HIT="$(find "$REPO" -type f \( -name '*document_to_program*' -o -name '*program_compiler*' -o -name '*strategy_compiler*' -o -name '*ingest_strategy*' \) 2>/dev/null | head -5)"
[ -n "$COMPILER_HIT" ] && ok "strategy→program compiler present" || bad "Document-to-Program compiler MISSING"

PROGRAM_RUNTIME_HIT="$(find "$REPO" -type f \( -name '*program_runtime*' -o -name '*StrategicInitiative*' \) 2>/dev/null | head -5)"
[ -n "$PROGRAM_RUNTIME_HIT" ] && ok "ProgramRuntime present" || bad "ProgramRuntime MISSING (expected $EXPECTED_PROGRAMS instances)"

# Morning briefing / feed generator (the "self-narration" surface)
FEED_HIT="$(find "$REPO" -type f \( -name '*morning_briefing*' -o -name '*feed_generator*' -o -name '*autonarrate*' \) 2>/dev/null | head -5)"
[ -n "$FEED_HIT" ] && ok "autonarration/feed surface present" || warn "no morning-briefing / feed generator found"

# Self-modifying loop: does the system WRITE new canon/policy candidates based on its own receipts?
SELF_LOOP="$(grep -rlE 'B_adaptive|promotion_candidate|autopoiesis|self_modify' "$REPO" --include='*.py' 2>/dev/null | head -5)"
[ -n "$SELF_LOOP" ] && ok "autopoietic self-loop surfaces present" || bad "autopoietic self-loop surfaces MISSING"

# =============================================================================
# 16. FILE_HEADER / COMMIT / TAG STANDARDS
# =============================================================================
sec "16 · Dignity IP Standards"
PUSH_SCRIPT="$REPO/scripts/axiolev_push.sh"
[ -f "$PUSH_SCRIPT" ] && ok "axiolev_push.sh present" || bad "axiolev_push.sh MISSING"

# Count .py files lacking AXIOLEV-FILE-HEADER
if have grep; then
  MISSING_HEADER=0
  while IFS= read -r f; do
    head -20 "$f" 2>/dev/null | grep -q "AXIOLEV" || MISSING_HEADER=$((MISSING_HEADER+1))
  done < <(find "$REPO" -type f -name '*.py' ! -path '*/.*' 2>/dev/null | head -500)
  say "- .py files (first 500) missing AXIOLEV header: **$MISSING_HEADER**"
  [ "$MISSING_HEADER" -eq 0 ] && ok "header compliance clean" || warn "header drift: $MISSING_HEADER files need header"
fi

# =============================================================================
# 17. TECH DEBT / DRIFT SIGNALS
# =============================================================================
sec "17 · Drift & Tech-Debt"
TODO_COUNT="$(grep -rEn 'TODO|FIXME|XXX' "$REPO" --include='*.py' 2>/dev/null | wc -l | tr -d ' ')"
say "- TODO/FIXME/XXX count (.py): **$TODO_COUNT**"

# =============================================================================
# 18. FOUNDER-READY DELTA MATRIX
# =============================================================================
sec "18 · Founder-Ready Delta Matrix"
cat >> "$REPORT_MD" <<'EOD'
| # | Acceptance Gate                                   | Source        | Status |
|---|---------------------------------------------------|---------------|--------|
| AC-1 | `canon/axioms/ax_core.json` with AX-1..AX-14     | Ring 6 §9      | see §2,§7 |
| AC-2 | `POST /pi/check` fail-closed on never-events     | Ring 6 §9      | see §4  |
| AC-3 | `POST /canon/promote` rejects insufficient ev.   | Ring 6 §9      | see §4  |
| AC-4 | Every consequential action has CPS receipt       | Ring 6 §9      | see §8  |
| AC-5 | Sentinel M1..M5 on 5-min cycle                   | Ring 6 §9      | see §4  |
| AC-6 | `/ns/resume` restores across ≥ 3 substitutions   | Ring 6 §9      | see §2,§4 |
| AC-7 | All new files under AXIOLEV-FILE-HEADER          | Ring 6 §9      | see §16 |
| D-1  | NER observable implemented (`ns_core/isr/ner.py`)| Doctrine Pt 1  | see §11 |
| D-2  | `force_ground` CPS lane implemented              | Doctrine Pt 2  | see §11 |
| D-3  | `HALLUCINATION_DOCTRINE.md` DRAFT-FOR-G5         | Doctrine Pt 3  | see §11 |
| CL-1 | Clearing Layer primitives (CI-1..CI-5)           | Clearing paper | see §12 |
| MAC  | launchd + menubar + shortcuts + hotkey           | Mac spec       | see §13 |
| UI   | NERTile + ForceGroundBanner + ClearingTile       | Doctrine §1.12 | see §14 |
| AP   | Compiler + ProgramRuntime + autonarration + loop | Symphony spec  | see §15 |
| VLK  | voice-loop-v1 intact (Polly.Matthew, SID, #)     | prior closure  | see §10 |
| YK1  | YubiKey slot_1 (26116460) bound                  | Ring 5         | see §9  |
| YK2  | YubiKey slot_2 provisioned                       | Ring 5         | PENDING HARDWARE |
EOD

# =============================================================================
# 19. RETURN BLOCK (machine-readable JSON for terminal-manager)
# =============================================================================
sec "19 · return-block-json"

cat > "$REPORT_JSON" <<EOF
{
  "return_block_version": 1,
  "worker_kind": "code_state_review",
  "stamp": "$STAMP",
  "host": "$(hostname 2>/dev/null || echo unknown)",
  "repo": "$REPO",
  "git": {
    "branch": "$GIT_BRANCH",
    "head": "$GIT_HEAD",
    "expected_branch": "$EXPECTED_BRANCH"
  },
  "services": {
    "docker_healthy": "${HEALTHY_COUNT:-0}",
    "docker_total": "${TOTAL_COUNT:-0}",
    "expected_healthy": $EXPECTED_SERVICES_COUNT
  },
  "doctrine": {
    "ner_impl_present": $([ -n "$NER_FILE" ] && echo true || echo false),
    "force_ground_impl_present": $([ -n "$FG_FILE" ] && echo true || echo false),
    "doctrine_md_present": $([ -f "$DOC_FILE" ] && echo true || echo false)
  },
  "ring6": {
    "ax_core_json": $([ -f "$REPO/canon/axioms/ax_core.json" ] && echo true || echo false),
    "never_event_corpus": $([ -d "$REPO/tests/pi/never_events" ] && echo true || echo false),
    "resume_ns_sh": $([ -f "$REPO/resume_ns.sh" ] && echo true || echo false),
    "axiolev_push_sh": $([ -f "$PUSH_SCRIPT" ] && echo true || echo false)
  },
  "voice_loop": {
    "respond_route": $(grep -rqE '/voice/respond' "$REPO" --include='*.py' 2>/dev/null && echo true || echo false),
    "polly_matthew": $(grep -rqE 'Polly\.Matthew' "$REPO" 2>/dev/null && echo true || echo false)
  },
  "ui": {
    "violet_panel": $([ -n "$UI_DIR" ] && echo true || echo false),
    "ner_tile": $([ -f "$REPO/ns_ui/violet_panel/components/NERTile.tsx" ] && echo true || echo false),
    "force_ground_banner": $([ -f "$REPO/ns_ui/violet_panel/components/ForceGroundBanner.tsx" ] && echo true || echo false),
    "clearing_tile": $([ -f "$REPO/ns_ui/violet_panel/components/ClearingTile.tsx" ] && echo true || echo false)
  },
  "mac_integration": {
    "launchd_plist": $([ -n "$LAUNCH_PLIST" ] && echo true || echo false),
    "menubar_artifact": $([ -n "$MENUBAR_HIT" ] && echo true || echo false),
    "shortcuts": $([ -n "$SHORTCUT_HIT" ] && echo true || echo false),
    "hotkey": $([ -n "$HOTKEY_HIT" ] && echo true || echo false)
  },
  "autopoiesis": {
    "compiler": $([ -n "$COMPILER_HIT" ] && echo true || echo false),
    "program_runtime": $([ -n "$PROGRAM_RUNTIME_HIT" ] && echo true || echo false),
    "autonarration": $([ -n "$FEED_HIT" ] && echo true || echo false),
    "self_loop": $([ -n "$SELF_LOOP" ] && echo true || echo false)
  },
  "yubikey": {
    "slot_1_expected": "$EXPECTED_YUBIKEY_SLOT1",
    "slot_2_status": "PENDING_HARDWARE"
  },
  "dignity_banner": "$DIGNITY"
}
EOF

code json
cat "$REPORT_JSON" >> "$REPORT_MD"
codeend

# =============================================================================
# 20. FOOT
# =============================================================================
sec "20 · Footer"
say "$DIGNITY"
say ""
say "**Report paths:**"
say "- Markdown: \`$REPORT_MD\`"
say "- JSON:     \`$REPORT_JSON\`"

# stdout terminal-manager handshake
echo "REPORT_PATH=$REPORT_MD"
echo "REPORT_JSON=$REPORT_JSON"
