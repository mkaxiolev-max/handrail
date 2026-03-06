#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[0] Activate venv"
source .venv/bin/activate

echo "[1] Ensure deps"
python -m pip -q install -U pip >/dev/null
python -m pip -q install -r requirements.txt

echo "[2] Audit: show current TwiML sources"
echo "---- twilio_voice.py has <Record>? ----"
python - <<'PY'
from pathlib import Path
p=Path("nss/interfaces/twilio_voice.py")
s=p.read_text()
print("<Record" in s)
PY

echo "---- server.py Redirects to /voice/transcription ----"
rg -n --no-heading '<Redirect[^>]*>.*voice/transcription</Redirect>' nss || true

echo "[3] Patch Arbiter: never crash on missing google_key"
python - <<'PY'
from pathlib import Path
import re
p = Path("nss/core/arbiter.py")
s = p.read_text()

# 3a) safest: replace "if self.google_key:" -> getattr(...)
s2 = s.replace("if self.google_key:", "if getattr(self, 'google_key', None):")

# 3b) if that pattern isn't present, ensure __init__ defines google_key = None
if s2 == s:
    # try to inject into __init__ if found
    m = re.search(r"def __init__\s*\(self[^)]*\):\n", s)
    if m:
        ins_at = m.end()
        # only add if not already present
        if "self.google_key" not in s[ins_at:ins_at+800]:
            s2 = s[:ins_at] + "        self.google_key = None\n" + s[ins_at:]
    else:
        s2 = s

if s2 != s:
    p.write_text(s2)
    print("Patched nss/core/arbiter.py (google_key safe).")
else:
    print("No arbiter patch needed (already safe or pattern not found).")
PY

echo "[4] Patch TwiML generator: force Gather speech loop + correct Redirect"
python - <<'PY'
from pathlib import Path
import re

p = Path("nss/interfaces/twilio_voice.py")
s = p.read_text()

# Replace the entire twiml_answer() body to Gather speech loop.
# Idempotent: if already Gather-based, keep.
def ensure_twiml_answer(src: str) -> str:
    if "def twiml_answer" not in src:
        raise SystemExit("twilio_voice.py missing def twiml_answer")

    # If it already has <Gather input="speech", keep but ensure Redirect target is /voice/incoming
    if '<Gather input="speech"' in src:
        src = re.sub(r'(<Redirect\b[^>]*>)([^<]*?/voice/transcription)(</Redirect>)',
                     lambda m: m.group(1)+m.group(2).replace("/voice/transcription","/voice/incoming")+m.group(3),
                     src)
        return src

    # Otherwise overwrite function implementation
    pattern = re.compile(r"def twiml_answer\s*\([^)]*\)\s*->\s*str:\s*.*?\n\s*return\s+f?\"\"\".*?\"\"\"\s*",
                         re.DOTALL)
    repl = '''def twiml_answer(gather_action: str) -> str:
    """
    TwiML to answer a call and gather speech input.
    """
    # Twilio speech gather MUST point to an absolute URL in production.
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech"
            action="{gather_action}"
            method="POST"
            timeout="6"
            speechTimeout="auto">
        <Say voice="Polly.Matthew" language="en-US">
            North Star online. How can I serve you?
        </Say>
    </Gather>
    <Say voice="Polly.Matthew" language="en-US">
        I did not catch that. Please try again.
    </Say>
    <Redirect method="POST">{NORTHSTAR_WEBHOOK_BASE}/voice/incoming</Redirect>
</Response>"""'''
    out, n = pattern.subn(repl, src, count=1)
    if n != 1:
        raise SystemExit("Failed to patch twiml_answer() automatically.")
    return out

# Ensure twiml_respond uses Gather (or at least does NOT rely on Record transcription callbacks)
def ensure_twiml_respond(src: str) -> str:
    if "def twiml_respond" not in src:
        return src
    # If it still contains <Record ... transcribeCallback, replace that block with a Gather loop
    if "<Record" in src and "def twiml_respond" in src:
        src = re.sub(
            r'(<Say[^>]*>\{message\}</Say>)(?:\s*<Record\b.*?>\s*)',
            r'\1',
            src,
            flags=re.DOTALL
        )
    return src

s2 = ensure_twiml_answer(s)
s2 = ensure_twiml_respond(s2)

# Also: any Redirect tags in this file pointing to /voice/transcription -> /voice/incoming
s2 = re.sub(r'(<Redirect\b[^>]*>)(https?://[^<]+)?/voice/transcription(</Redirect>)',
            r'\1\2/voice/incoming\3', s2)

if s2 != s:
    p.write_text(s2)
    print("Patched nss/interfaces/twilio_voice.py (Gather loop + redirect).")
else:
    print("No twilio_voice.py changes needed.")
PY

echo "[5] Patch server TwiML wrappers: Gather action must be absolute (base + path)"
python - <<'PY'
from pathlib import Path
import re

p = Path("nss/api/server.py")
s = p.read_text()

# Ensure twiml_answer_for / twiml_respond_for use base + absolute
# They already do, but we ensure no relative action="/voice/transcription" survives in wrappers.
s2 = s

# Fix any Redirect tags anywhere in nss/ that point to /voice/transcription -> /voice/incoming
# (server.py sometimes emits redirects)
s2 = re.sub(r'(<Redirect\b[^>]*>)(https?://[^<]+)?/voice/transcription(</Redirect>)',
            r'\1\2/voice/incoming\3', s2)

# Fix voice_transcription behavior: if SpeechResult missing, redirect back to /voice/incoming (not hangup)
# Find the specific block:
# if not session or not transcript: return Response(content=twiml_hangup_for(), ...)
s2 = re.sub(
    r'if not session or not transcript:\s*\n\s*return Response\(content=twiml_hangup_for\(\), media_type="application/xml"\)',
    'if not session or not transcript:\n            return Response(content=twiml_answer_for(get_or_create_session(call_sid, caller, os.environ.get("TWILIO_PHONE_NUMBER",""))), media_type="application/xml")',
    s2
)

if s2 != s:
    p.write_text(s2)
    print("Patched nss/api/server.py (redirect + missing transcript flow).")
else:
    print("No server.py changes needed.")
PY

echo "[6] Regen helper files: 4-terminal runbook + smoke tests"
cat > scripts/TERMINALS_4_RUNBOOK.txt <<'TXT'
TERMINAL A (SERVER)
cd /Volumes/NSExternal/NSS
source .venv/bin/activate
lsof -ti tcp:9000 | xargs kill -9 2>/dev/null || true
uvicorn nss.api.server:app --host 0.0.0.0 --port 9000 --reload --log-level info

TERMINAL B (NGROK)
ngrok http 9000

TERMINAL C (HEALTH + LOG QUICKCHECK)
curl -s http://127.0.0.1:9000/voice/health | python -m json.tool
curl -s http://127.0.0.1:9000/sms/health   | python -m json.tool

TERMINAL D (VOICE TWIML SMOKE)
NGROK="https://YOUR_NGROK_URL"
curl -s -X POST "$NGROK/voice/incoming" -d "CallSid=CA_TEST" -d "From=+15551234567" -d "To=+15557654321"
TXT

cat > scripts/voice_smoke.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
NGROK="${1:-}"
if [[ -z "$NGROK" ]]; then
  echo "usage: scripts/voice_smoke.sh https://xxxx.ngrok-free.dev"
  exit 1
fi
curl -s -X POST "$NGROK/voice/incoming" \
  -d "CallSid=CA_TEST" \
  -d "From=+15551234567" \
  -d "To=+15557654321" | sed -n '1,180p'
SH
chmod +x scripts/voice_smoke.sh

echo "[7] Done. Next: restart server + verify TwiML."
