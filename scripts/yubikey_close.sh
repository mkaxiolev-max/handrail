#!/usr/bin/env bash
# NS∞ YubiKey Hardware Close — physical OTP validation
# Usage: touch your YubiKey, then run this script and paste the OTP when prompted

set -euo pipefail

NS_URL="http://localhost:9000"

echo ""
echo "=== NS∞ YubiKey Hardware Close ==="
echo ""
echo "YubiKey detected: $(ykman list 2>/dev/null || echo 'not detected')"
echo ""
echo "1. Place cursor in terminal"
echo "2. TOUCH the YubiKey gold button"
echo "3. The key will type a 44-char OTP automatically"
echo "4. Paste it below (or it may auto-submit)"
echo ""

# Check if OTP was passed as arg (e.g., piped in after key touch)
if [ -n "${1:-}" ]; then
    OTP="$1"
else
    read -p "Paste OTP here: " OTP
fi

OTP="${OTP// /}"  # strip spaces
echo ""
echo "Testing OTP: ${OTP:0:12}... (${#OTP} chars)"
echo ""

RESULT=$(curl -s -X POST "$NS_URL/auth/yubikey" \
    -H "Content-Type: application/json" \
    -d "{\"otp\": \"$OTP\"}")

echo "$RESULT" | python3 -m json.tool

OK=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('ok',''))" 2>/dev/null)

if [ "$OK" = "True" ] || [ "$OK" = "true" ]; then
    echo ""
    echo "✅ HARDWARE CLOSE: ok=true — YubiCloud validation LIVE"
    TOKEN=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null)
    echo "   Token: $TOKEN"
else
    echo ""
    echo "⚠️  HARDWARE CLOSE: validation failed — check OTP freshness"
    exit 1
fi
