# NS∞ Launch Sequence
**Execute after all 5 ACTIVATION_CHECKLIST steps are complete**

---

## Pre-Launch Verification (30 min before posting)

```bash
# 1. Final sovereign boot check
curl -s -X POST http://localhost:8011/ops/cps \
  -H 'Content-Type: application/json' \
  -d @.cps/sovereign_boot.json | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(f'boot: {d[\"expect_result\"][\"passed\"]}')"

# 2. Verify payment links are live (charges process)
curl -s https://buy.stripe.com/4gM5kwghB9703rebLAfjG04 | grep -i "checkout\|amount" | head -3

# 3. Verify ROOT checkout endpoint
curl -s -X POST https://root-jade-kappa.vercel.app/api/checkout \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@test.com","plan":"pro"}' | python3 -m json.tool

# 4. All 3 URLs responding 200
curl -s -o /dev/null -w "%{http_code} " https://zeroguess.dev
curl -s -o /dev/null -w "%{http_code} " https://root-jade-kappa.vercel.app
curl -s -o /dev/null -w "%{http_code}\n" https://axiolevruntime.vercel.app
```

---

## Day 1–5: ROOT Launch

### Twitter / X
```
ROOT is live.

State layer for the agentic era.

Know exactly what's broken. In seconds.
root.axiolev.com
```

```
ROOT v1:
→ reads your system state
→ identifies root cause with confidence score
→ tells you the fix + time estimate
→ executes it (Pro)

curl -s root.axiolev.com/install | bash

Free to start. Pro at $49/mo.
```

### Hacker News — Show HN
**Title:** `Show HN: ROOT – deterministic state diagnosis for AI agents and dev environments`

**Body:**
```
ROOT reads your system state, identifies the exact root cause of failures,
scores confidence, estimates time-to-fix, and optionally executes the fix.

Built on Handrail (our deterministic CPS execution engine) — every diagnosis
and auto-fix is Merkle-logged with cryptographic proof.

Free tier: diagnosis only. Pro ($49/mo): auto-fix execution.
Auto ($99/mo): continuous monitoring + pre-emptive fixes.

root.axiolev.com | curl install | source on github.com/mkaxiolev-max
```

### Reddit — r/programming + r/MachineLearning
Cross-post the HN link within 1 hour of posting.

---

## Day 6–10: Handrail Launch

### Twitter / X
```
Handrail is live.

Execution control plane for LLM agents.

1000/1000 deterministic. Merkle-logged. ABI-enforced.
axiolevruntime.vercel.app
```

```
What Handrail gives you:
→ every agent action is a signed CPS op
→ Merkle chain of every execution
→ ABI schema enforcement at the boundary
→ YubiKey-gated R3/R4 risk ops
→ 125 ops across 25 domains

The execution layer you can trust absolutely.
$29/mo Pro · $299/mo Enterprise
```

### Hacker News — Show HN
**Title:** `Show HN: Handrail – deterministic CPS execution control for LLM agents`

**Body:**
```
Handrail is an execution control plane for AI agents. Every operation is a
typed CPS (Continuation-Passing Style) op — logged, proven, and reproducible.

Core guarantees:
- 1000/1000 deterministic outputs verified (Merkle-chained proof ledger)
- ABI schema enforcement: CPSPacket is the ONLY artifact crossing the
  intelligence→execution boundary
- YubiKey-gated R3/R4 risk operations (financial, destructive, irreversible)
- 125 ops across 25 domains (fs, http, git, docker, Slack, email, Stripe, SMS...)
- Dignity Kernel: constitutional never-events enforced at boot

Free tier available. Pro $29/mo. Enterprise $299/mo.

axiolevruntime.vercel.app | github.com/mkaxiolev-max
```

---

## Revenue Targets

| Milestone | Timeline | Signups | MRR |
|-----------|----------|---------|-----|
| First paying customer | Day 3 | 1 | $49 |
| ROOT traction | Day 5 | 10 ROOT Pro | **$490 MRR** |
| Handrail traction | Day 10 | 10 ROOT + 10 Handrail Pro | **$780 MRR** |
| Combined scale | Day 30 | 30 ROOT + 25 Handrail + 5 Enterprise | **$3,920 MRR** |
| Series A proof | Month 3 | 200 total | **$14K+ MRR** |

---

## Post-Launch Monitoring

```bash
# Check Stripe revenue (after keys are live)
curl -s -X POST http://localhost:8011/ops/cps \
  -H 'Content-Type: application/json' \
  -d '{"cps_id":"check_revenue","ops":[{"op":"stripe.get_balance","args":{}},{"op":"stripe.list_payments","args":{}}]}'

# Check NS∞ voice / SMS activity
curl -s http://localhost:9000/voice/sessions
curl -s http://localhost:9000/memory/recent?n=10

# Founder Console (live monitoring)
open http://localhost:9000/founder
```
