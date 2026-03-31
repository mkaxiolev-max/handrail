# NS∞ AXIOLEV — LAUNCH CHECKLIST

## ✅ COMPLETED

- [x] CPSExecutor 500 fixed — execution engine proven
- [x] Voice loop — gather + Claude + re-gather (voice-loop-v1)
- [x] YubiKey binding + YubiCloud validation (yubikey-cloud-v1)
- [x] Dignity Kernel never-events (dignity-kernel-v1)
- [x] Alexandria boot proof (alexandria-v1)
- [x] Alexandria → NSExternal SSD (alexandria-ssd-v1)
- [x] OP_DISPATCH consolidated (cps-dispatch-v1)
- [x] YubiKey quorum on boot.runtime (quorum-v1)
- [x] boot.sh cold start verified — macOS Docker socket fix (boot-cold-v1)
- [x] Continuum hardened — /continuum/status, tier escalation routes, SSD persistence (continuum-v1)
- [x] CLAUDE.md architecture brief created (claude-md-v1)
- [x] Voice session persistence to NSExternal (voice-sessions-v1)
- [x] CPS determinism 1000/1000 verified (determinism-v1)
- [x] noguess.dev → zeroguess.dev domain fix (domain-fix-v1)
- [x] ROOT landing page audited — viewport, mobile, Stripe links live (root-prelaunch-v1)
- [x] Handrail landing page audited — fixed placeholder CTA, added mobile CSS (handrail-prelaunch-v1)
- [x] NSExternal volume mounted in Docker — verified from inside containers (ssd-mount-v1)
- [x] DOCKER_HOST persisted in .env and boot.sh (docker-host-v1)
- [x] watchdog.sh + LaunchAgent com.axiolev.watchdog (watchdog-v1)
- [x] /health/full unified status endpoint — ok=true, all services healthy (health-full-v1)
- [x] FOUNDER_PHONE=+13602310554 wired for TIER_F voice detection (founder-phone-v1)

## ⚠️ REMAINING BLOCKERS

- [ ] **Stripe account activation** — required for payment processing on Pro/Auto/Enterprise tiers
- [ ] **Custom domains** — `root-jade-kappa.vercel.app` → final domain (root.axiolev.com or root.so); `axiolevruntime.vercel.app` → handrail.axiolev.com
- [ ] **Physical YubiKey close** — touch key → `curl -X POST localhost:9000/auth/yubikey -H 'X-YSK-Token: <otp>'` → ok:true
- [ ] **YUBIKEY_CLIENT_ID** — not set in .env (yubikey.serial_set=true but client_id_set=false)
- [ ] **HN launch post** — pending HN availability and copy review
- [ ] **Free tier signup flow** — "Get Started" links to GitHub; no free tier registration path

## LAUNCH TARGETS

| Product | URL | Status |
|---------|-----|--------|
| ROOT | https://root-jade-kappa.vercel.app | Live |
| Handrail | https://axiolevruntime.vercel.app | Live |
| Hub | https://zeroguess.dev | Live |
| Voice | +1 (307) 202-4418 | Live |
| NS∞ Dashboard | http://localhost:9000 | Local |
| NS∞ ngrok | https://monica-problockade-caylee.ngrok-free.dev | Live |

## ARCHITECTURE

```
Handrail (8011) → NS (9000) → Continuum (8788)
SSD: /Volumes/NSExternal/ALEXANDRIA/
     ├── snapshots/      ← boot proof (local + SSD mirror)
     ├── ledger/         ← ns_receipt_chain.jsonl + watchdog.log
     ├── sessions/       ← voice session persistence
     ├── continuum/      ← tier state + event streams
     └── ether/          ← document ingest
```

## RUN

```bash
# Cold start
./boot.sh

# Verify
curl http://localhost:9000/health/full | python3 -m json.tool

# Watchdog
launchctl list | grep axiolev
```
