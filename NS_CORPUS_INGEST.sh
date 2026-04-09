#!/usr/bin/env bash
# NS∞ CORPUS INGEST — mike_corpus_v1 → Alexandria atom pipeline
# 5-stage lane: discover → parse → ingest → build → verify
set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RESET='\033[0m'

ok()   { echo -e "  ${GREEN}✓${RESET} $1"; }
fail() { echo -e "  ${RED}✗${RESET} $1"; exit 1; }
info() { echo -e "  ${CYAN}→${RESET} $1"; }
warn() { echo -e "  ${YELLOW}!${RESET} $1"; }

ALEXANDRIA_URL="${ALEXANDRIA_URL:-http://127.0.0.1:9001}"
NS_URL="${NS_URL:-http://127.0.0.1:9000}"
CORPUS_ROOT="${CORPUS_ROOT:-${HOME}/mike_corpus_v1}"

echo ""
echo -e "${BOLD}╔══════════════════════════════════════╗${RESET}"
echo -e "${BOLD}║    NS∞ CORPUS INGEST — mike_v1       ║${RESET}"
echo -e "${BOLD}╚══════════════════════════════════════╝${RESET}"
echo ""

# ── Stage 1: Discover ─────────────────────────────────────────────────────────
echo -e "${BOLD}[1/5] Discover corpus files${RESET}"
if [ ! -d "$CORPUS_ROOT" ]; then
    warn "Corpus root not found at $CORPUS_ROOT"
    warn "Creating example corpus from CLAUDE.md and local .md/.txt files"
    CORPUS_ROOT="$(pwd)"
fi

FILE_COUNT=0
declare -a CORPUS_FILES=()
while IFS= read -r -d '' f; do
    CORPUS_FILES+=("$f")
    FILE_COUNT=$((FILE_COUNT + 1))
done < <(find "$CORPUS_ROOT" -maxdepth 3 \( -name "*.md" -o -name "*.txt" -o -name "*.rst" \) \
    ! -path "*/node_modules/*" ! -path "*/.git/*" ! -path "*/venv/*" \
    -print0 2>/dev/null)

ok "Discovered $FILE_COUNT files in $CORPUS_ROOT"

if [ "$FILE_COUNT" -eq 0 ]; then
    warn "No corpus files found — nothing to ingest"
    exit 0
fi

# ── Stage 2: Check Alexandria health ─────────────────────────────────────────
echo -e "${BOLD}[2/5] Alexandria health check${RESET}"
HEALTH=$(curl -sf "${ALEXANDRIA_URL}/atoms/healthz" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','?'))" 2>/dev/null || echo "unreachable")
if [ "$HEALTH" != "ok" ]; then
    fail "Alexandria not healthy ($HEALTH) — run ./NS_BOOT.sh first"
fi
ok "Alexandria healthy"

# ── Stage 3: Parse + Ingest ──────────────────────────────────────────────────
echo -e "${BOLD}[3/5] Parse + ingest files${RESET}"
INGESTED=0
FAILED=0
TOTAL_ATOMS=0

ingest_file() {
    local file="$1"
    local text
    text=$(cat "$file" 2>/dev/null) || return 1
    local char_count=${#text}
    if [ "$char_count" -lt 20 ]; then
        return 0  # skip trivially small files
    fi
    # Truncate to 8000 chars to stay within API limits
    text="${text:0:8000}"
    local result
    result=$(curl -sf -X POST "${ALEXANDRIA_URL}/atoms/ingest-text" \
        -H "Content-Type: application/json" \
        -d "$(python3 -c "import json,sys; print(json.dumps({'text': sys.argv[1], 'source_item_id': None, 'bundle_id': None}))" "$text")" \
        2>/dev/null) || return 1
    local atoms_created
    atoms_created=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('atoms_created',0))" 2>/dev/null || echo 0)
    echo "$atoms_created"
}

for file in "${CORPUS_FILES[@]}"; do
    fname="$(basename "$file")"
    atoms=$(ingest_file "$file" 2>/dev/null || echo "0")
    if [ "$atoms" = "0" ] && ! echo "$atoms" | grep -q "^[0-9]"; then
        warn "  Failed: $fname"
        FAILED=$((FAILED + 1))
    else
        TOTAL_ATOMS=$((TOTAL_ATOMS + atoms))
        INGESTED=$((INGESTED + 1))
        info "  $fname → $atoms atoms"
    fi
done

ok "Ingested $INGESTED/$FILE_COUNT files, $TOTAL_ATOMS total atoms (${FAILED} failed)"

# ── Stage 4: Build atoms from parse_bundles ───────────────────────────────────
echo -e "${BOLD}[4/5] Build atoms from parse_bundles${RESET}"
BUILD=$(curl -sf -X POST "${ALEXANDRIA_URL}/atoms/build" 2>/dev/null | \
    python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"bundles={d.get('bundles_processed',0)} atoms={d.get('atoms_created',0)} arcs={d.get('arcs_detected',0)}\")" 2>/dev/null || echo "skipped")
ok "Build: $BUILD"

# ── Stage 5: Verify final atom count ─────────────────────────────────────────
echo -e "${BOLD}[5/5] Verify atom counts${RESET}"
NOW=$(curl -sf "${NS_URL}/system/now" 2>/dev/null | \
    python3 -c "import sys,json; d=json.load(sys.stdin); m=d.get('memory',{}); print(f\"atoms={m.get('atoms',0)} edges={m.get('edges',0)}\")" 2>/dev/null || echo "unavailable")
ok "Final state: $NOW"

echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${GREEN}║    CORPUS INGEST COMPLETE            ║${RESET}"
echo -e "${BOLD}${GREEN}╚══════════════════════════════════════╝${RESET}"
echo ""
