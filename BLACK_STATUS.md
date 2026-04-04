# BLACK Commercial Closure Status
**Date:** 2026-04-04 | **Author:** NS∞ autonomous closure run

---

## 1. Permanent Webhook

| Field | Value |
|-------|-------|
| **Status** | CONFIRMED |
| **URL** | `https://monica-problockade-caylee.ngrok-free.dev` |
| **Mechanism** | macOS LaunchAgent `com.axiolev.ngrok` |
| **LaunchAgent PID** | 1075 |
| **Config** | `KeepAlive=true`, `RunAtLoad=true` |
| **Plist path** | `~/Library/LaunchAgents/com.axiolev.ngrok.plist` |
| **ngrok domain type** | Free static domain (ngrok-free.dev) — permanent for authtoken lifetime |

---

## 2. Twilio Phone Number +1 (307) 202-4418

| Field | Value | Status |
|-------|-------|--------|
| **voice_url** | `https://monica-problockade-caylee.ngrok-free.dev/voice/inbound` | CONFIRMED |
| **sms_url** | `https://monica-problockade-caylee.ngrok-free.dev/sms/inbound` | CONFIRMED |
| **sms_fallback_url** | `https://monica-problockade-caylee.ngrok-free.dev/sms/inbound` | CONFIRMED (fixed from `/voice/incoming`) |
| **Phone SID** | `PN4b6a0454077b913d749804047aab8061` | — |

---

## 3. Stripe Environment

| Field | Value | Status |
|-------|-------|--------|
| **STRIPE_SECRET_KEY** | `STRIPE_SK_PENDING` (placeholder in `.env`) | PENDING — manual key entry required |
| **STRIPE_PUBLISHABLE_KEY** | `STRIPE_PK_PENDING` (placeholder in `.env`) | PENDING — manual key entry required |
| **stripe_integration.py** | Reads `STRIPE_SECRET_KEY` from env; `create_subscription()` + `verify_subscription()` implemented | CODE READY |
| **Placeholder price ID** | `price_1ABC123XYZ` in `stripe_integration.py:17` | PENDING — replace with real Stripe Price IDs |

Keys must be obtained from `dashboard.stripe.com` and manually substituted in `.env` before Ring 5 go-live.

---

## 4. Vercel Deployments

| URL | HTTP | Purpose | Stripe Links |
|-----|------|---------|--------------|
| `https://zeroguess.dev` | **200** | Hub — routes to ROOT + Handrail pages | None (nav hub only) |
| `https://root-jade-kappa.vercel.app` | **200** | ROOT landing — prices shown ($49/mo Pro, $99/mo Auto) | **NONE** — CTAs link to `root.axiolev.com` (DNS fails) |
| `https://axiolevruntime.vercel.app` | **200** | Handrail landing — Stripe payment links wired | **2 live links** (see below) |

---

## 5. Payment Links in Pages

### axiolevruntime.vercel.app (Handrail) — WIRED
| Plan | Price | Link | Status |
|------|-------|------|--------|
| Pro | $29/mo | `https://buy.stripe.com/4gM5kwghB9703rebLAfjG04` | Live — charges blocked pending LLC verification |
| Enterprise | $299/mo | `https://buy.stripe.com/dRmaEQlmHfwc6Dq6rgfjG06` | Live — charges blocked pending LLC verification |

### root-jade-kappa.vercel.app (ROOT) — NOT WIRED
- Prices displayed: Pro $49/mo, Auto $99/mo
- CTA button: `→ Get ROOT` → links to `https://root.axiolev.com`
- `root.axiolev.com` — **DNS resolution fails** (domain not configured)
- **Gap:** ROOT has no working Stripe payment link path

### zeroguess.dev (Hub) — PASS-THROUGH
- No direct Stripe links; routes visitors to `root-jade-kappa.vercel.app` and `axiolevruntime.vercel.app`

---

## 6. Remaining Manual Actions for Ring 5 Go-Live

1. **[REVENUE BLOCKER] Complete Stripe LLC business verification**
   - URL: `https://dashboard.stripe.com`
   - Impact: both `buy.stripe.com` payment links are live but charges are blocked until verified
   - Estimated time: 1–3 business days after submission

2. **[REVENUE BLOCKER] Substitute live Stripe keys into `.env`**
   - Set `STRIPE_SECRET_KEY=sk_live_...` and `STRIPE_PUBLISHABLE_KEY=pk_live_...`
   - Obtain from `dashboard.stripe.com → Developers → API Keys`

3. **[REVENUE BLOCKER] Replace placeholder price ID in `stripe_integration.py`**
   - File: `stripe_integration.py:17`
   - Replace `price_1ABC123XYZ` with real Stripe Price IDs for Pro ($29/mo) and Enterprise ($299/mo)
   - Create price objects at `dashboard.stripe.com → Products`

4. **[REVENUE BLOCKER] Wire ROOT payment links into `root-jade-kappa.vercel.app`**
   - Add `buy.stripe.com` links for ROOT Pro ($49/mo) and Auto ($99/mo)
   - Fix or remove the broken `root.axiolev.com` CTA — DNS is not configured

5. **[OPTIONAL] Configure `root.axiolev.com` domain**
   - Currently DNS resolution fails entirely
   - Either point to Vercel deployment or remove from CTAs

6. **[QUORUM BLOCKER] Procure and enroll 2nd YubiKey (Slot 2)**
   - Hardware: YubiKey 5 NFC
   - Command: `python3 scripts/yubikey_bind.py --enroll --slot 2`
   - Impact: 2-of-2 quorum not achievable; production NS boot requires quorum expansion

7. **[HYGIENE] Mark GitHub secret scanning false positives**
   - URL: `https://github.com/mkaxiolev-max/handrail/security/secret-scanning`
   - Targets: `omega-checkpoint-v1`, `sms-channel-v1` tags
   - Non-blocking for revenue launch

8. **[LAUNCH] Execute public announcement sequence**
   - Twitter/X: `"Handrail + NS∞ are live. Deterministic AI execution. zeroguess.dev"`
   - HN: `"Show HN: Handrail — deterministic execution control plane for AI agents"`
   - Reddit r/MachineLearning: cross-post HN link

---

## Summary

| Gate | Status |
|------|--------|
| Permanent webhook | ✅ CONFIRMED — PID 1075, LaunchAgent KeepAlive |
| Twilio webhook | ✅ CONFIRMED — all 3 URLs correct |
| Vercel deployments (3) | ✅ CONFIRMED — all 200 |
| Handrail payment links | ✅ WIRED — 2 Stripe links live |
| ROOT payment links | ❌ BROKEN — root.axiolev.com DNS fails |
| Stripe env keys | ⏳ PENDING — placeholders in .env.example |
| Stripe LLC verification | ⏳ PENDING — charges blocked |
| Price IDs in code | ⏳ PENDING — placeholder in stripe_integration.py |
| YubiKey slot 2 | ⏳ PENDING — hardware not procured |
