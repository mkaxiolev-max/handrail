#!/usr/bin/env bash
# NS∞ Final Operational Closure Validation
# Usage: ./scripts/final_validation.sh

PASS=0
FAIL=0

ok()   { echo "  ✓ $1"; PASS=$((PASS+1)); }
fail() { echo "  ✗ $1"; FAIL=$((FAIL+1)); }

echo "=== NS∞ FINAL VALIDATION $(date '+%Y-%m-%d %H:%M:%S') ==="
echo ""

# 1. Containers
echo "[ CONTAINERS ]"
UP=$(docker compose -f "$(dirname "$0")/../docker-compose.yml" ps 2>/dev/null | grep -c "Up\|running" || true)
[ "$UP" -ge 7 ] && ok "Containers: $UP/7 running" || fail "Containers: only $UP/7 running"

echo ""

# 2. Healthz endpoints
echo "[ SERVICE HEALTH ]"
for port in 9000 9001 9002 9004 9005; do
  status=$(curl -s --connect-timeout 3 "http://127.0.0.1:$port/healthz" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','?'))" 2>/dev/null || echo "")
  if [ "$status" = "ok" ] || [ "$status" = "healthy" ]; then
    ok ":$port /healthz → $status"
  else
    fail ":$port /healthz → ${status:-no-response}"
  fi
done

echo ""

# 3. Postgres
echo "[ POSTGRES ]"
docker compose -f "$(dirname "$0")/../docker-compose.yml" exec -T postgres psql -U ns -d ns -c "SELECT 1" > /dev/null 2>&1 \
  && ok "Postgres accessible (ns@ns)" \
  || fail "Postgres not accessible"

echo ""

# 4. Ollama
echo "[ OLLAMA ]"
MODEL_COUNT=$(curl -s --connect-timeout 3 http://127.0.0.1:11434/api/tags 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('models',[])))" 2>/dev/null || echo "0")
[ "$MODEL_COUNT" -ge 3 ] && ok "Ollama: $MODEL_COUNT/3 models loaded" || fail "Ollama: only $MODEL_COUNT/3 models"

echo ""

# 5. Feed build
echo "[ FEED BUILD ]"
FEED_RESULT=$(curl -s --connect-timeout 5 -X POST http://127.0.0.1:9000/feed/build 2>/dev/null || echo "")
FEED_STATUS=$(echo "$FEED_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','?'))" 2>/dev/null || echo "")
FEED_CARDS=$(echo "$FEED_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('cards_inserted',0))" 2>/dev/null || echo "0")
[ "$FEED_STATUS" = "ok" ] && ok "Feed built: $FEED_CARDS cards inserted" || fail "Feed build failed: ${FEED_STATUS:-no-response}"

echo ""

# 6. Receipt chain verify
echo "[ RECEIPT CHAIN ]"
CHAIN_RESULT=$(curl -s --connect-timeout 5 http://127.0.0.1:9005/integrity/verify 2>/dev/null || echo "")
CHAIN_STATUS=$(echo "$CHAIN_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','?'))" 2>/dev/null || echo "")
CHAIN_LEN=$(echo "$CHAIN_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('chain_length',0))" 2>/dev/null || echo "0")
[ "$CHAIN_STATUS" = "ok" ] && ok "Receipt chain verified: $CHAIN_LEN receipts, unbroken" || fail "Receipt chain: ${CHAIN_STATUS:-no-response}"

echo ""

# 7. Git
echo "[ GIT ]"
cd "$(dirname "$0")/.."
COMMIT=$(git log --oneline -1 2>/dev/null || echo "")
[ -n "$COMMIT" ] && ok "Git: $COMMIT" || fail "Git: no commits found"

echo ""

# Summary
echo "[ SUMMARY ]"
TOTAL=$((PASS + FAIL))
echo "  Passed: $PASS / $TOTAL"
if [ "$FAIL" -eq 0 ]; then
  echo ""
  echo "  ✓ All systems ready — NS First Operational Closure validated"
  exit 0
else
  echo ""
  echo "  ⚠ $FAIL check(s) failed — review above before tagging"
  exit 1
fi
