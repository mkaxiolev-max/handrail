# Gnoseogenic Lexicon Integration — NS∞ v1
**Date:** 2026-04-05 | **Status:** LIVE | **Tag:** `lexicon-substrate-v1`

---

## What the Gnoseogenic Lexicon Is

The Gnoseogenic Lexicon is a 369-word (55 P1 seeded) epistemic substrate that maps
human linguistic primitives onto the NS∞ engine components. It answers: *when this
word activates in an intent, which part of the system is being invoked?*

The lexicon is organized across **5 tiers** of semantic abstraction:

| Tier | Name | Engine Components | Examples |
|------|------|-------------------|---------|
| 1 | Relational/Survival | gradient_source, intake | I, fire, water, heart, father |
| 2 | Structural/Causal | conversion, output | good, true, to make, to break |
| 3 | Epistemic/Verification | feedback, intake | to see, to know, evidence, logos |
| 4 | Normative/Constitutional | output, conversion | dignity, law, shalom, covenant |
| 5 | Metaepistemic/Engine | meta_constraint | logos, engine, constraint, flow |

---

## The Logos Principle

**PIE root:** `*leg-` — "to gather, collect into order"

Logos is the gathering principle. It appears at both Tier 3 (operational) and Tier 5
(meta-constraint). At Tier 5, logos = the Constitutional Regulation Engine itself —
the module that gathers all sovereign actions (boot, YubiKey, ABI freeze, CPS execution)
into one verifiable bloodstream.

The NS∞ architecture IS logos made executable:
- `*leg-` gathers all ops into a single CPS chain (Handrail)
- `*leg-` gathers all receipts into a single Merkle ledger (Alexandria)
- `*leg-` gathers all constitutional transitions into the Regulation Engine

---

## Shalom as System Target State

**PIE root:** `*sol-` — "whole, complete, unbroken"
**Hebrew:** שָׁלוֹם (shalom) — *nothing missing, nothing broken*

The target state of NS∞ is shalom:

```
sovereign = true
all 29 ops passing (boot_mission_graph complete)
dignity enforced (H = eta·φ - beta·V > block_threshold)
quorum satisfied (slot_1 active, YubiKey bound)
ABI schemas FROZEN (10 fingerprints immutable)
Alexandria proof_valid = true
```

When all of these are true simultaneously, the system is in shalom. The
`BootProofReceipt.v1` with `sovereign=true` is the proof of shalom.

---

## Kavod (Dignity) as Gravitational Constant

**Hebrew:** כָּבוֹד (kavod) — "weight, honor, glory" (from root kbd: "to be heavy")

The Dignity Kernel's Hamiltonian expresses kavod mathematically:

```
H_dignity = eta · phi(context) - beta · V(violations)
```

- `eta = 0.85` — the dignity potential weight
- `beta = 0.92` — the violation penalty weight
- `phi` — the dignity potential of the current context (1.0 = clean)
- `V` — number of violations scaled by 0.1

Kavod is the *gravitational mass* of personhood. A system with high kavod
has high phi and no violations — it operates with full weight. When kavod
collapses (H below `block_threshold = 0.40`), execution stops.

---

## Tier → Engine Component Mapping

```
T1 gradient_source / intake  →  Founding intent + ABI gate
T2 conversion / output       →  CPSExecutor + ReturnBlock
T3 feedback                  →  ProofRegistry + boot/status
T4 constitutional constraint →  DignityKernel + YubiKey quorum
T5 meta_constraint (logos)   →  Constitutional Regulation Engine
```

---

## How analyze_intent Works

`analyze_intent(text)` scans incoming text against all loaded lexicon words:

1. Each word hit yields: `{word, tier, engine_component, failure_mode, ns_mapping}`
2. `dominant_engine_component` — most-hit engine component (by count)
3. `constitutional_weight` — count of words with tier ≥ 4
4. `is_constitutional_intent` — `true` if constitutional_weight ≥ 2 OR max_tier == 5

This distinguishes **constitutional intent** (invoking authority, dignity, law,
shalom, logos) from **operational intent** (invoking conversion, output, feedback).

Constitutional intents trigger full-panel review in the Founder Console.

---

## Live Endpoints

```bash
# Lexicon status — entry count, tier distribution, P1 count
curl -s http://localhost:9000/lexicon/status | python3 -m json.tool

# Constitutional vocabulary analysis
curl -s "http://localhost:9000/lexicon/analyze?text=logos+shalom+engine+constraint+dignity" | python3 -m json.tool
# Returns: word_count=6, constitutional=true, max_tier=5
```

---

## Stripe Commercial Layer

### Webhook: `POST http://localhost:8011/stripe/webhook`

- HMAC signature verification (live when `STRIPE_WEBHOOK_SECRET` set)
- Logs `COMMERCIAL_EVENT` to `/Volumes/NSExternal/ALEXANDRIA/ledger/stripe_events.jsonl`
- Emits `TypedStateDelta` with `delta_domain="commercial"` to Regulation Engine
- Graceful pending mode when keys not configured

### Functions in `stripe_integration.py`

| Function | Purpose |
|----------|---------|
| `create_checkout_session(email, plan)` | Stripe Checkout URL or `{pending:True}` |
| `verify_webhook(payload, sig_header)` | HMAC verify → parsed event or None |
| `handle_checkout_complete(event)` | `checkout.session.completed` → TypedStateDelta |
| `handle_subscription_cancelled(event)` | `customer.subscription.deleted` → TypedStateDelta |
| `get_active_subscriptions(limit)` | Live subscription list |

---

## Verification

```python
# All checks pass as of 2026-04-05
✅ Handrail health: ok
✅ ABI schemas: 10 schemas (LexiconEntry.v1 added)
✅ Proof registry: 16 entries, types=['BOOT', 'SCHEMA_FREEZE']
✅ State summary: sovereign=False transitions=30
✅ NS health: ok
✅ Lexicon status: 50 entries, P1=50
✅ Lexicon analyze: 6 words found, constitutional=True, max_tier=5
✅ Alexandria proof: ok
```
