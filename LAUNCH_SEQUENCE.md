# NS∞ / ROOT / HANDRAIL — Launch Sequence
**Execute after Ring 5 all clear | Target: $3.9K MRR by Day 30**

---

## Pre-launch gate
```bash
curl https://root-jade-kappa.vercel.app/api/system-status | python3 -c "import sys,json; d=json.load(sys.stdin); print('launch_ready:', d['launch_ready'])"
curl http://localhost:8011/system/status | python3 -c "import sys,json; d=json.load(sys.stdin); print('shalom:', d['shalom'], d['shalom_score'])"
```
Expected: `launch_ready: true` and `shalom: True 8/8`

---

## Days 1–5: ROOT launch

### Day 1 — HN Show HN
**Title:** "Show HN: ROOT – deterministic execution receipts for AI agents"
**Body outline:**
- Problem: AI agents take actions you can't audit or replay
- ROOT: every op gets a run_id, SHA256 intent hash, deterministic replay
- Open source core, $49/mo Pro
- Link: https://zeroguess.dev

**Post at:** 9 AM ET Monday (peak HN traffic)
**Watch:** https://news.ycombinator.com/newest — respond to every comment within 30 min

### Day 2 — Twitter/X thread
Account: @AXIOLEV (create if not exists)
Thread: "We've been building something unusual..." → determinism proof → screenshot → zeroguess.dev → "DM for early access"

### Day 3 — Reddit
- r/MachineLearning: "ROOT: auditable execution for AI agents"
- r/LangChain: "Alternative to hoping your agent did the right thing"
- r/programming: "Deterministic AI execution with SHA256 receipts"

### Day 4 — Direct outreach
GitHub search: `filename:requirements.txt langchain` / `filename:package.json autogen`
Message: "Building on [framework]? ROOT gives you auditable receipts for every agent action. Free tier at zeroguess.dev."

### Day 5 — Review and iterate
- Check Stripe dashboard for signups
- If <5 signups: adjust HN post title and repost

**Day 5 target: 10 ROOT Pro signups → $490 MRR**

---

## Days 6–10: Handrail launch

### Day 6 — HN Show HN (Handrail)
**Title:** "Show HN: Handrail – policy-enforced execution governor for AI systems"
**Link:** https://axiolevruntime.vercel.app

### Day 7-8 — Developer communities
- AI engineer Discord servers
- GitHub Discussions on LangChain, AutoGen, CrewAI
- LinkedIn: "What if your AI system could prove it followed the rules?"

### Day 9-10 — Enterprise outreach
Target: AI engineering leads at mid-market companies ($299/mo Enterprise)

**Day 10 target: +20 Handrail Pro → total $1,070 MRR**

---

## Days 11–30: Compound

| Day | Action | Target MRR |
|-----|--------|-----------|
| 15 | +5 ROOT Auto, referral outreach | $1,565 |
| 20 | +10 Handrail Pro, LinkedIn paid post | $1,855 |
| 25 | First Enterprise close (Stewart leads) | $2,755 |
| 30 | Organic + 2nd Enterprise | $3,900 |

---

## First Enterprise path (Stewart Weston)
1. Stewart identifies 3 target companies (AI agent builders with compliance risk)
2. Elaine makes initial contact (commercial program state S1_OPEN)
3. Follow commercial_cps_program_v1 exactly — no improvisation
4. Position: "constitutional AI execution" not "AI governance tool"
5. Pricing: $2,500/mo site license minimum, annual preferred

---

## Commercial program state machine (reference)
```
S0_IDENTIFY → S1_OPEN → S2_FRAME → S3_QUALIFY → S4_CHAMPION
    → S5_VALIDATION (heidi) → S6_NEGOTIATION (stewart) → S7_CLOSE → S8_COMMIT → S9_ARCHIVE

Roles:
  elaine_access_operator:       S0–S4 (default)
  heidi_validation_operator:    S4–S5 (skepticism trigger only)
  stewart_negotiation_operator: S4–S8 (pricing/structure trigger)
  legal_operator:               S7–S8
  founder:                      S5–S7 (escalation only)

Launch whisper panel:
  python3 whisper_panel.py commercial_cps_program_v1
```

---

## Monitoring during launch
```bash
curl -s http://localhost:8011/system/status | python3 -c "
import sys,json; d=json.load(sys.stdin)
print(f'shalom: {d[\"shalom\"]} | transitions: {d[\"regulation\"][\"total_transitions\"]}')"

open https://dashboard.stripe.com/revenue
python3 voice_webhook_health.py
```
