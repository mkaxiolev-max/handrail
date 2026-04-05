#!/usr/bin/env python3
"""
Voice webhook health check — verifies Twilio webhook is reachable.
Permanent deployment: use Vercel serverless (recommended) or ngrok (fallback).
Target line: +1(307)202-4418 | Account SID: see TWILIO_ACCOUNT_SID env var
"""
import urllib.request, json, subprocess, os
from pathlib import Path

NGROK_DOMAIN = "monica-problockade-caylee.ngrok-free.dev"
TWILIO_SID = os.environ.get("TWILIO_ACCOUNT_SID", "AC***redacted***")
VOICE_LINE = "+13072024418"

def check_ngrok():
    try:
        r = urllib.request.urlopen(f"https://{NGROK_DOMAIN}/health", timeout=5)
        return r.status == 200, f"https://{NGROK_DOMAIN}"
    except Exception as e:
        return False, str(e)

def check_ns_voice():
    try:
        r = urllib.request.urlopen("http://localhost:9000/voice/health", timeout=3)
        d = json.loads(r.read())
        return d.get("ok", False), d
    except Exception as e:
        return False, str(e)

def ensure_ngrok_running():
    """Ensure ngrok tunnel is active. Start if not."""
    ok, url = check_ngrok()
    if ok:
        print(f"  [OK] ngrok tunnel live: {url}")
        return True

    print(f"  [WARN] ngrok tunnel not responding: {url}")
    print("  Starting ngrok tunnel...")
    try:
        proc = subprocess.Popen([
            "ngrok", "http", "--domain", NGROK_DOMAIN, "9000"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import time; time.sleep(3)
        ok2, url2 = check_ngrok()
        if ok2:
            print(f"  [OK] ngrok started: {url2}")
            return True
        else:
            print(f"  [WARN] ngrok did not come up: {url2}")
            print(f"  Manual: ngrok http --domain {NGROK_DOMAIN} 9000")
            return False
    except FileNotFoundError:
        print("  [WARN] ngrok not in PATH")
        print(f"  Install: brew install ngrok/ngrok/ngrok")
        print(f"  Then: ngrok http --domain {NGROK_DOMAIN} 9000")
        return False

def print_status():
    print("=" * 56)
    print("VOICE WEBHOOK STATUS")
    print("=" * 56)
    print(f"Twilio line:    {VOICE_LINE}")
    print(f"Account SID:    {TWILIO_SID}")
    print(f"ngrok domain:   {NGROK_DOMAIN}")

    ngrok_ok, ngrok_url = check_ngrok()
    print(f"ngrok tunnel:   {'✅ LIVE' if ngrok_ok else '❌ DOWN'} {ngrok_url if ngrok_ok else ''}")

    voice_ok, voice_data = check_ns_voice()
    print(f"NS voice:       {'✅ READY' if voice_ok else '⚠️  DOWN'}")

    webhook_url = f"https://{NGROK_DOMAIN}/twilio/voice"
    print(f"\nTwilio webhook: {webhook_url}")
    print(f"Set at: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming")
    print(f"Voice URL: {webhook_url}")
    print("=" * 56)

if __name__ == "__main__":
    import sys
    if "--ensure" in sys.argv:
        ensure_ngrok_running()
    print_status()
