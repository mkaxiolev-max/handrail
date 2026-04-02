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

## Docker Compose

```bash
# Cold start
docker-compose down --remove-orphans && ./boot.sh

# Rebuild single service
DOCKER_HOST="unix:///Users/${USER}/.docker/run/docker.sock" docker-compose build ns
docker-compose up -d ns
```
