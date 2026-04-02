# NS∞ — AXIOLEV Holdings | Architecture Brief
<!-- Copyright © 2026 Axiolev. All rights reserved. Proprietary and confidential. -->

## Architecture

```
Handrail (8011) → NS (9000) → Continuum (8788)
```

- **Handrail** (`services/handrail/`) — CPS execution engine, policy enforcement, auth gateway, CLI interface
- **NS (NorthStar)** (`services/ns/`) — Constitutional AI OS: Arbiter, receipts, voice lane, ether ingest, SAN terrain
- **Continuum** (`services/continuum/`) — Append-only event store + TierLatch (0=active, 2=isolated, 3=suspended; ratchet only up)

All containers mount `/Volumes/NSExternal` for SSD persistence.

## Boot

```bash
./boot.sh
```

Full cold start: Docker check → build → health-wait → ngrok → Twilio webhook.
Produces `NS∞ BOOT COMPLETE` banner when all 3 containers healthy.

## Key Files

| File | Purpose |
|------|---------|
| `services/handrail/handrail/server.py` | Handrail FastAPI app, `/ops/cps`, `/healthz` |
| `services/ns/nss/api/server.py` | NorthStar FastAPI app, all NS endpoints |
| `services/continuum/src/server.py` | Continuum FastAPI app, `/state`, `/continuum/status` |
| `services/ns/nss/core/receipts.py` | ReceiptChain — append-only audit ledger |
| `services/ns/nss/core/storage.py` | Alexandria root resolution (SSD > ~/ALEXANDRIA) |
| `services/handrail/handrail/cps_engine.py` | CPS op executor |

## Git: Force-Add Ignored Service Files

```bash
git add -f services/handrail/handrail/server.py
git add -f services/ns/nss/api/server.py
git add -f services/continuum/src/server.py
```

Many service files are gitignored but must be tracked. Always use `git add -f` for service changes.

## CPS Plans

| Plan | Location | Purpose |
|------|----------|---------|
| `health_check` | `.cps/health_check.json` | Service health: handrail, ns, continuum |
| `ns_boot_v1` | `.cps/ns_boot_v1.json` | Full NS boot sequence verification |

Execute via: `POST http://localhost:8011/ops/cps` with plan JSON body.

## YubiKey Auth

```
POST /auth/yubikey
Header: X-YSK-Token: <token>
```

Required for `boot.runtime` operations. Validates via YubiCloud OTP. Bound to `YUBIKEY_CLIENT_ID` + `YUBIKEY_SECRET_KEY` env vars.

## Alexandria

- **Root**: `/Volumes/NSExternal/ALEXANDRIA/` (SSD) or `~/ALEXANDRIA/` (fallback)
- **Snapshots**: `/Volumes/NSExternal/ALEXANDRIA/snapshots/` — boot proof snapshots
- **Ledger**: `/Volumes/NSExternal/ALEXANDRIA/ledger/ns_receipt_chain.jsonl` — receipt mirror (append-only)
- **Ether**: `/Volumes/NSExternal/ALEXANDRIA/ether/` — document ingest store
- **Status**: `GET http://localhost:9000/alexandria/status`

## Never-Events

These operations are constitutionally prohibited — never implement, route, or execute:

- `dignity.never_event` — any action violating human dignity invariants
- `sys.self_destruct` — irreversible system destruction
- `auth.bypass` — authentication or authorization bypass
- `policy.override` — CPS policy gate override without conciliar quorum

## Endpoints Quick-Ref

| Service | Endpoint | Notes |
|---------|---------|-------|
| Handrail | `GET /healthz` | Health check |
| Handrail | `POST /ops/cps` | Execute CPS plan |
| NS | `GET /healthz` | Health check |
| NS | `GET /alexandria/status` | Snapshot + ledger counts |
| NS | `GET /health/alexandria` | SSD mount check |
| NS | `POST /auth/yubikey` | YubiKey OTP validation |
| NS | `GET /voice/sessions` | Active + persisted sessions |
| Continuum | `GET /state` | TierLatch state |
| Continuum | `GET /continuum/status` | Full structured status |
| Continuum | `POST /append` | Append event to stream |
| Continuum | `POST /receipts` | Append receipt to operational stream |

## Meet Adapter — POST /meet/transcript

Turns meeting transcripts into NS intent. Observe or respond.

```json
{"speaker": "John", "text": "NS, what do you think?", "meeting_id": "mtg_001"}
```

Returns: `{action: "respond"|"observe"|"escalate", session_id, response}`

Architecture: Human → `/meet/transcript` → NS intent classifier → Handrail/CPS → response

## Adapter Registry (CPS OP_DISPATCH)

All ops routed through `POST /ops/cps` via `cps_engine.py`:

| Domain | Op | Notes |
|--------|----|-------|
| `fs` | `fs.pwd` | Current working directory |
| `fs` | `fs.list` | Directory listing (policy-gated path) |
| `fs` | `fs.read` | File read (policy-gated path) |
| `git` | `git.status` | Porcelain status for repo |
| `git` | `git.log` | Recent commits |
| `git` | `git.diff` | Diff stat vs ref |
| `git` | `git.commit` | Commit with message (mutation policy required) |
| `proc` | `proc.run_readonly` | Run allowlisted read-only command |
| `proc` | `proc.run_allowed` | Run allowlisted command (policy-gated) |
| `docker` | `docker.compose_ps` | List compose services |
| `docker` | `docker.compose_up` | Start compose services (mutation policy required) |
| `http` | `http.get` | HTTP GET |
| `http` | `http.post` | HTTP POST with JSON body |
| `http` | `http.health_check` | Health check with expect_status |
| `sys` | `sys.env_get` | Read allowlisted env var (masked) |
| `sys` | `sys.disk_usage` | Disk usage for path |
| `sys` | `sys.uptime` | System uptime |
| `slack` | `slack.post_message` | Post to Slack webhook URL |
| `slack` | `slack.notify` | Notify founder via SLACK_WEBHOOK_URL |
| `email` | `email.send` | Send email via SMTP |
| `email` | `email.notify` | Notify FOUNDER_EMAIL via SMTP |
| `stripe` | `stripe.get_balance` | Stripe account balance |
| `stripe` | `stripe.list_customers` | List Stripe customers |
| `stripe` | `stripe.list_payments` | List Stripe payment intents |
| `schedule` | `schedule.run_at` | Schedule a CPS plan at ISO8601 time |
| `schedule` | `schedule.list` | List scheduled plans |
| `schedule` | `schedule.cancel` | Cancel scheduled plan by plan_id |

| `ns` | `ns.sms_send` | Send SMS via Twilio to a number |
| `ns` | `ns.voice_call` | Initiate outbound Twilio call |
| `ns` | `ns.memory_query` | Search NS /memory/search with q param |
| `ns` | `ns.memory_recent` | Get last N memory entries from NS |
| `ns` | `ns.broadcast` | Send same message via SMS + console |

**32 ops across 11 domains.** Graceful skip on unconfigured external services (Slack, email, Stripe, Twilio).

## Docker Compose

```bash
# Cold start
docker-compose down --remove-orphans && ./boot.sh

# Rebuild single service
DOCKER_HOST="unix:///Users/${USER}/.docker/run/docker.sock" docker-compose build ns
docker-compose up -d ns
```
