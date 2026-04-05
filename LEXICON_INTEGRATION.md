# Gnoseogenic Lexicon Integration — NS∞ v1
**Date:** 2026-04-05 | **Status:** LIVE | **Sprint:** `ns-infinity-final-v1`

---

## Summary

The Gnoseogenic Lexicon is now wired into the NS∞ runtime. 30 P1 semantic primitives
across 5 tiers are loaded from Alexandria SSD and accessible via live API endpoints.

---

## Files Created / Modified

| File | Action | Purpose |
|------|--------|---------|
| `scripts/seed_lexicon.py` | **Created** | 30 P1 entries, POST to NS or fallback JSONL |
| `abi/schemas/LexiconEntry.v1.json` | **Created** | ABI schema for lexicon entries |
| `services/ns/nss/lexicon_substrate.py` | **Created** | Load + index + analyze lexicon |
| `services/ns/nss/api/server.py` | **Modified** | Added `/lexicon/status` + `/lexicon/analyze` |
| `services/ns/nss/ui/founder.py` | **Modified** | LEXICON panel (panel 13) + analyze widget |
| `stripe_integration.py` | **Modified** | Full commercial layer: checkout, webhook, subscriptions |
| `services/handrail/handrail/server.py` | **Modified** | `POST /stripe/webhook` with Continuum emit |

---

## Live Endpoints

| Endpoint | Method | Notes |
|----------|--------|-------|
| `http://localhost:9000/lexicon/status` | GET | 30 entries, 5 tiers, 5 components |
| `http://localhost:9000/lexicon/analyze?text=` | GET | Intent analysis against lexicon |

---

## Lexicon Structure

### 30 P1 Entries — 5 Tiers × 6 Words

| Tier | Engine Component | Words |
|------|-----------------|-------|
| 1 | `gradient_source` | gnosis, arche, logos, telos, axiom, nomos |
| 2 | `intake` | aisthesis, krinein, schema, hyle, mneme, kairos |
| 3 | `conversion` | poiesis, praxis, synthesis, methodos, aletheia, kinesis |
| 4 | `output` | apodeixis, entelecheia, eidos, ergon, apophasis, mimesis |
| 5 | `meta_constraint` | dikaiosyne, sophrosyne, phronesis, autonomia, harmonia, kathekon |

### ABI Schema: `LexiconEntry.v1`
- `entry_id`: `LEX-[A-Z0-9]{8}`
- `word`, `tier` (1–5), `pie_root`, `semitic` (optional)
- `cognitive_act`, `engine_component` (enum: 7 values)
- `failure_mode`, `priority` (P1–P5)
- `ns_mapping`: `{service, module, cps_op}`
- `timestamp`

### Seed Path
- Primary: `/Volumes/NSExternal/.run/lexicon_seeds.jsonl`
- Fallback: `~/.axiolev/lexicon_seeds.jsonl`
- Fingerprint: `a7998c3ca2c4fc00`

---

## Stripe Commercial Layer

### New functions in `stripe_integration.py`

| Function | Purpose |
|----------|---------|
| `create_checkout_session(email, plan, ...)` | Stripe Checkout URL, graceful pending state |
| `verify_webhook(payload, sig_header)` | HMAC signature verify → parsed event |
| `handle_checkout_complete(event)` | `checkout.session.completed` → TypedStateDelta |
| `handle_subscription_cancelled(event)` | `customer.subscription.deleted` → TypedStateDelta |
| `get_active_subscriptions(limit)` | List live subscriptions with customer email |

### Plans wired

| Plan key | Env var | Product |
|----------|---------|---------|
| `handrail_pro` | `STRIPE_PRICE_ID_HANDRAIL_PRO` | Handrail Pro $29/mo |
| `handrail_enterprise` | `STRIPE_PRICE_ID_HANDRAIL_ENT` | Handrail Enterprise $299/mo |
| `root_pro` | `STRIPE_PRICE_ID_ROOT_PRO` | ROOT Pro $49/mo |
| `root_auto` | `STRIPE_PRICE_ID_ROOT_AUTO` | ROOT Auto $99/mo |

### Webhook endpoint

```
POST http://localhost:8011/stripe/webhook
Header: stripe-signature: <Stripe-generated>
```

Emits TypedStateDelta receipts to Continuum (`POST /receipts`) on `checkout.session.completed`
and `customer.subscription.deleted`.

---

## Founder Console

LEXICON panel (panel 13) added between DIGNITY CONFIG and FOUNDER ACTIONS:
- Shows entry count, loaded status, tier breakdown, component breakdown
- Inline analyze widget: type text → see matched words + failure modes
- Refreshes every 60s

---

## Verification

```bash
# Lexicon status
curl -s http://localhost:9000/lexicon/status | python3 -m json.tool

# Intent analysis
curl -s "http://localhost:9000/lexicon/analyze?text=gnosis+is+the+arche+of+logos" | python3 -m json.tool

# Re-seed lexicon
python3 scripts/seed_lexicon.py
```

Expected:
- `entry_count: 30`
- `loaded: true`
- analyze returns `words_found`, `tiers_present`, `dominant_engine_component`, `failure_modes_detected`
