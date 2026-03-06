NORTHSTAR Boot Guide v2
NS∞ · AXIOLEV Holdings · Constitutional AI Operating System
═══════════════════════════════════════════════════════════

PREREQUISITES (one-time)
─────────────────────────
1. Install Python 3.11+
   brew install python@3.11

2. Install ngrok (for inbound voice calls)
   brew install ngrok/ngrok/ngrok
   ngrok config add-authtoken YOUR_NGROK_TOKEN
   (Get token at: https://dashboard.ngrok.com/get-started/your-authtoken)

3. Install ykman (optional, for YubiKey hardware auth)
   brew install ykman

4. Install credentials
   python3 ~/NSS/ns_setup.py
   → Opens http://localhost:9001
   → Paste all API keys
   → Click Save → writes ~/NSS/.env + macOS Keychain


FIRST BOOT
──────────
1. Extract NSS_v2.tar.gz:
   cd ~ && tar -xzf ~/Downloads/NSS_v2.tar.gz

2. Copy launcher to Desktop:
   cp ~/NSS/NORTHSTAR.command ~/Desktop/

3. Double-click NORTHSTAR.command
   → Terminal opens automatically
   → Set founder password on first boot
   → Server starts on port 9000
   → ngrok tunnel opens
   → Twilio webhook auto-configured
   → Lexicon v0.1 bootstrapped
   → Dashboard opens in browser

4. Open Console on iPhone/iPad:
   Safari → http://[your-mac-ip]:9000/console
   Login: founder / [your password]


SUBSEQUENT BOOTS
────────────────
Double-click NORTHSTAR.command
Takes ~15 seconds to be fully online.


INTERFACES
──────────
Dashboard:   http://localhost:9000
  Quick system status, credential management, arbiter query

Console:     http://localhost:9000/console
  Full multi-user cockpit — Chat, Receipts, Approvals, Visuals, Canon
  Works on iPhone/iPad Safari
  Login with role-based access control

Voice (Computer):  Call +1 (307) 202-4418
  Tier-gated, SafeSpeak filtered
  Whisper coach mode, action confirmation ritual

WebSocket:   ws://localhost:9000/ws?token=YOUR_TOKEN
  Real-time event stream for native apps (Phase 3)


KEY ENDPOINTS
─────────────
POST /auth/login          Login, get token
GET  /health              Full system health
GET  /lexicon/summary     SFE lexicon state
GET  /receipts            Receipt chain (last 50)
GET  /approvals/pending   Pending approvals
POST /chat/send           Arbiter query
GET  /canon/proposals     Canon proposals
WS   /ws?token=           WebSocket event stream


TROUBLESHOOTING
───────────────
Server won't start:
  tail -50 ~/NSS/logs/server.log

ngrok not connecting:
  Check ~/.config/ngrok/ngrok.yml for authtoken
  Or: ngrok config add-authtoken YOUR_TOKEN

Twilio webhook not set:
  After boot: curl http://localhost:9000/health/voice

Voice not working:
  1. Check ngrok URL in health response
  2. Verify Twilio credentials in ~/NSS/.env
  3. Check Twilio console: console.twilio.com

Console login fails:
  Default password: northstar
  Changed via first-boot prompt or:
  curl -X POST http://localhost:9000/auth/login \
    -H "Content-Type: application/json" \
    -d '{"user_id":"founder","password":"northstar"}'

Rotate credentials without reboot:
  Dashboard → Diagnostics → ROTATE (per key)
  Or: curl -X POST http://localhost:9000/credential/update \
    -H "Authorization: Bearer TOKEN" \
    -d '{"key":"ANTHROPIC_API_KEY","value":"sk-ant-..."}'


SYSTEM ARCHITECTURE
───────────────────
Layer 1: Intelligence  — Arbiter (Claude + GPT-4o + Gemini + Grok)
Layer 2: Memory        — Alexandria (ether, receipts, SFE lexicon)
Layer 3: Interface     — Computer voice lane + Console + Dashboard
Layer 4: Action        — Alpaca trading (paper mode, founder veto)
Layer 5: Governance    — Auth/roles, Canon, Conciliar Amendment v1.0

Semantic substrate: SFE (Socratic Field Engine)
  Concepts versioned, boundaries outcome-bound, conflicts first-class
  /lexicon/* endpoints. Bootstrap: POST /lexicon/bootstrap


CREDENTIAL KEYS REQUIRED
─────────────────────────
ANTHROPIC_API_KEY      console.anthropic.com/settings/keys
OPENAI_API_KEY         platform.openai.com/api-keys
GOOGLE_API_KEY         console.cloud.google.com/apis/credentials
GROK_API_KEY           console.x.ai
TWILIO_ACCOUNT_SID     console.twilio.com
TWILIO_AUTH_TOKEN      console.twilio.com
TWILIO_PHONE_NUMBER    +13072024418 (or your number)
ALPACA_API_KEY         app.alpaca.markets/paper
ALPACA_API_SECRET      app.alpaca.markets/paper
POLYGON_API_KEY        polygon.io/dashboard/api-keys
FRED_API_KEY           fredaccount.stlouisfed.org/apikeys
NEWSAPI_KEY            newsapi.org/account
NORTHSTAR_PORT         9000 (default)

Optional:
NS_FOUNDER_PASSWORD    Set on first boot (default: northstar)
YUBIKEY_SERIAL         Auto-detected on boot
NGROK_AUTHTOKEN        Set via: ngrok config add-authtoken TOKEN
