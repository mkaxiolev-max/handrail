#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

FAIL=0

echo "=== docker compose ps ==="
docker compose ps || FAIL=1
echo

H_JSON="$(curl -fsS http://127.0.0.1:8011/healthz 2>/dev/null || true)"
N_JSON="$(curl -fsS http://127.0.0.1:9000/healthz 2>/dev/null || true)"
C_JSON="$(curl -fsS http://127.0.0.1:8788/state 2>/dev/null || true)"

echo "=== handrail ==="
echo "${H_JSON:-DOWN}"
echo

echo "=== ns ==="
echo "${N_JSON:-DOWN}"
echo

echo "=== continuum ==="
echo "${C_JSON:-DOWN}"
echo

python3 - <<'PY' "$H_JSON" "$N_JSON" "$C_JSON" || FAIL=1
import json, sys

def parse(s):
    try:
        return json.loads(s) if s else None
    except Exception:
        return None

h = parse(sys.argv[1])
n = parse(sys.argv[2])
c = parse(sys.argv[3])

ok = True

if not (isinstance(h, dict) and h.get("ok") is True):
    print("FAIL: handrail healthz not ok=true")
    ok = False
else:
    print("PASS: handrail healthz ok=true")

if not (isinstance(n, dict) and n.get("status") == "ok"):
    print("FAIL: ns healthz status!=ok")
    ok = False
else:
    print("PASS: ns healthz status=ok")

storage = (n or {}).get("storage") if isinstance(n, dict) else {}
if not (isinstance(storage, dict) and storage.get("external_ssd") is True):
    print("FAIL: ns storage.external_ssd!=true")
    ok = False
else:
    print("PASS: ns storage.external_ssd=true")

if not isinstance(c, dict):
    print("FAIL: continuum state not json object")
    ok = False
else:
    print("PASS: continuum state reachable")

raise SystemExit(0 if ok else 1)
PY

echo
if [ "$FAIL" -eq 0 ]; then
  echo "BOOT_STATUS=PASS"
  exit 0
else
  echo "BOOT_STATUS=FAIL"
  exit 1
fi
