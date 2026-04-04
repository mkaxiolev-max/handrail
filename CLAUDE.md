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
| `ns` | `ns.proactive_intel` | Jarvis: 3 Haiku-generated suggestions from system state |
| `ns` | `ns.capability_graph` | Full capability graph nodes + summary |
| `ns` | `ns.flywheel` | Invention flywheel state (unresolved, candidates, SAN) |
| `ns` | `ns.explain_recent` | Recent NS decision explanations |
| `ns` | `ns.semantic_candidates` | Semantic feedback binder candidates |

**37 ops across 11 domains.** Graceful skip on unconfigured external services (Slack, email, Stripe, Twilio).

| `audio` | `audio.get_volume` | AppleScript: output volume; graceful skip if not macOS |
| `audio` | `audio.set_volume` | AppleScript: set volume; Dignity Guard: 0–100 range |
| `audio` | `audio.get_playing` | AppleScript: Music track; graceful skip if not running |
| `clipboard` | `clipboard.read` | pbpaste; Dignity Guard: strips sk_/whsec_ secrets |
| `clipboard` | `clipboard.write` | pbcopy; Dignity Guard: max 10000 chars |
| `notify` | `notify.send` | AppleScript: display notification; graceful skip if not macOS |
| `notify` | `notify.badge` | AppleScript: dock tile badge; graceful skip if not macOS |

| `display` | `display.get_info` | system_profiler + osascript brightness; graceful skip if not macOS |
| `display` | `display.set_brightness` | AppleScript set brightness; Dignity Guard: 0.0–1.0 |
| `display` | `display.screenshot_info` | Quartz/CoreGraphics via python3; graceful skip if no Quartz |
| `battery` | `battery.get_status` | pmset -g batt; graceful skip if no battery/not macOS |
| `battery` | `battery.get_power_source` | pmset -g ps; graceful skip if not macOS |
| `keychain` | `keychain.check_entry` | security find-generic-password exit code only; Dignity Guard: never returns secret; blocks shell metacharacters |
| `keychain` | `keychain.list_services` | security dump-keychain svce lines only; Dignity Guard: strips pass/pwd/secret/token/key lines |
| `vision` | `vision.screenshot` | screencapture -x → artifact PNG; Dignity Guard: screen_recording required |
| `vision` | `vision.ocr_region` | screencapture region → tesseract OCR; graceful skip if no tesseract |

| `alert` | `alert.dialog` | Modal dialog with custom buttons; returns button pressed; max 500 chars |
| `alert` | `alert.confirm` | Yes/No confirm dialog; returns bool |
| `alert` | `alert.input` | Text input dialog; returns value (never logged — Dignity Guard) |
| `calendar` | `calendar.list` | List all calendar names via osascript |
| `calendar` | `calendar.today` | Today's events; graceful skip if no permission |
| `calendar` | `calendar.upcoming` | Next N events (max 20); 7-day window |
| `contacts` | `contacts.search` | Search contacts by name/email; max 10 results; read-only |
| `contacts` | `contacts.count` | Total contact count |
| `contacts` | `contacts.vcard` | Export contact as vCard; name+email only |
| `reminders` | `reminders.list` | List incomplete reminders; graceful skip on no permission |
| `reminders` | `reminders.add` | Add reminder; max 200 chars dignity guard |
| `reminders` | `reminders.complete` | Complete reminder by exact name match; no bulk ops |
| `url` | `url.open` | Open URL in browser; https only, no file/javascript schemes |
| `url` | `url.fetch` | Fetch URL content; timeout 10s, max 5000 chars |
| `url` | `url.qr` | Generate QR code PNG (base64); https only |
**73 ops across 25 domains** (Mac adapter bridge: audio.*, clipboard.*, notify.*, display.*, battery.*, keychain.*, env.permissions, vision.* — graceful skip when adapter not running).

Formalization layer: `adapter_core/capability_registry.py` (38 ops typed/versioned), `adapter_core/artifact_writer.py` (path+hash+size+ts).

## Dignity Kernel — YubiKey Binding (BLACK KNIGHT Step 4)

File: `services/ns/nss/kernel/dignity.py`

```
YubikeyQuorum — 2-of-3 quorum model
  slot_1: serial 26116460 (primary, ACTIVE)
  slot_2: pending (backup)
  slot_3: pending (emergency)
Threshold: 1-of-1 active. Expands to 2-of-3 when 2nd key provisioned.
```

Challenge flow: `GET /kernel/yubikey/challenge` → 32-byte nonce, TTL=5min
Verify flow:    `POST /kernel/yubikey/verify` with `{otp, challenge_id}` → `{verified, receipt_id}`
Status:         `GET /kernel/yubikey/status` → serial, quorum_slots, quorum_satisfied

**R3/R4 risk tier gate** — enforced in `CPSExecutor.execute` BEFORE Dignity Kernel never-event check:
- CPS payload fields: `risk_tier` (R0–R4), `yubikey_verified` (bool)
- R3 or R4 without `yubikey_verified: true` → `POLICY_DENIAL`, `failure_events.jsonl`
- R0–R2: no YubiKey required

Receipts written to: `/Volumes/NSExternal/ALEXANDRIA/ledger/kernel_decisions.jsonl`

## Program Library v1 (10 namespaces, 68 ops + 5 meta)

State stored at `/Volumes/NSExternal/ALEXANDRIA/programs/{namespace}/{instance_id}.jsonl`

| Namespace | Op count | Special guardrail |
|-----------|----------|-------------------|
| `fundraising` | 7 | — |
| `hiring` | 7 | — |
| `partner` | 7 | — |
| `ma` | 7 | `ma.close_transaction` requires `args.approval_ref` |
| `advisor` | 6 | — |
| `cs` | 7 | — |
| `feedback` | 7 | — |
| `gov` | 7 | `gov.record_decision` + `gov.issue_constraint` require `policy_profile: founder` |
| `knowledge` | 8 | `knowledge.promote_to_canon` requires `args.confirmed: true` |

Meta-contract (all namespaces): `program.advance_state`, `program.flag_risk`, `program.request_approval`, `program.log_receipt`, `program.archive`

**125 total CPS ops** (32 existing + 68 program + 5 meta + 7 Mac adapter bridge v3: audio/clipboard/notify + 7 Mac adapter bridge v4: display/battery/keychain + 5 sys.* direct + 1 env.permissions).

## Model Router

Registry: `services/ns/nss/models/registry.py` — 5 models (guardian/analyst/forge/critic/generalist)

| Intent class | Models selected |
|-------------|-----------------|
| `voice_quick` | analyst |
| `voice_action` | analyst, critic |
| `strategy` | analyst, forge, critic |
| `high_risk` | all enabled |
| `default` | analyst |

Veil gate strips secrets from context before local (guardian) model calls.
Outcome receipts written to `/Volumes/NSExternal/ALEXANDRIA/ledger/model_decisions.jsonl`.

## M2 Jarvis State

- **Proactive greeting**: voice_inbound pulls memory context, greets with last session topic
- **Memory context in responses**: router prepends cross-session context to all Anthropic calls
- **POST /intel/suggest**: `{topic, context}` → 3+ suggestions via strategy routing
- **GET /ops/recent**: last 5 CPS execution summaries
- **GET /models/registry + /models/status**: live model health
- **Founder Console v2**: WS live badge, models in health panel, last 3 ops, memory feed
- **Failure classification**: all OP_DISPATCH failures classified → `failure_events.jsonl`
- **Temporal validity gate**: `_memory_clock` auto-refreshes if >5 min stale

## Three-Reality Architecture (v5 canonical)
- Lexicon (semantic reality): canonical meanings, USDL gate library, state capsule
- Alexandria (knowledge reality): receipts, sessions, MaRS dual-lattice, canon, provenance
- SAN (legal/territorial reality): territory nodes, claim coordinates, whitespace, risk zones, filings, licensing targets
- NS synchronizes all three. Architecture law: owning words → owning knowledge → owning territory.

## SAN Adapter (san namespace — 8 ops)
`san.add_territory`, `san.map_claim`, `san.find_whitespace`, `san.flag_risk`,
`san.file_intent`, `san.add_licensing_target`, `san.query_territory`, `san.sync_with_lexicon`
State: `/Volumes/NSExternal/ALEXANDRIA/san/` (fallback: `~/.axiolev/san/`)

## Semantic Feedback Binder
Path: `services/ns/nss/semantic/feedback_binder.py`
Every execution run produces: (1) operational receipt + (2) semantic update candidate
Objects: `ExecutionOutcome` → `SemanticImpactReport` → `MeaningRefinementCandidate` → `CanonCommitProposal`
Endpoints: `GET /semantic/candidates`, `GET /semantic/proposals`, `POST /semantic/promote`

## Capability Graph
Path: `services/ns/nss/capability/graph.py`
18 nodes, 9 states. Missingness is explicit state.
Endpoints: `GET /capability/graph`, `GET /capability/unresolved`, `POST /capability/update`
Top unresolved (by strategic_value): usdl_decoder_live (8), 2nd_yubikey (8), policy_evolution (7)

## Ring Completion Status

| Ring | Name | Status | Milestone |
|------|------|--------|-----------|
| Ring 1 | Foundations | ✅ COMPLETE | M1 Founder MVP — boot, voice, receipts, Alexandria, Handrail CPS |
| Ring 2 | Intelligence | ✅ COMPLETE | M2 Jarvis — Program Library v1, Model Router, Proactive Intel, Console v2 |
| Ring 3 | Sovereign | ✅ COMPLETE | BLACK KNIGHT — YubiKey quorum, Dignity Kernel, Continuum v1, Boot Proof |
| Ring 4 | Capability | ✅ COMPLETE | Adapter expansion, SAN, Semantic Binder, determinism/perf/crash proofs |
| Ring 5 | Production | ⛔ BLOCKED | Stripe live keys, production domain, legal entity formation |

## BLACK KNIGHT Milestones

| Step | Name | Status |
|------|------|--------|
| Step 1 | Constitutional Boot | ✅ Complete |
| Step 2 | Receipt Chain | ✅ Complete |
| Step 3 | Alexandria Merkle Proof | ✅ Complete |
| Step 4 | YubiKey Binding — 2-of-3 quorum, R3/R4 gate, live YubiCloud | ✅ Complete |
| Step 5 | Dignity Kernel — NE1/NE2/NE3/NE4 never-events, NS Boot Proof, Continuum v1 | ✅ Complete |

Sovereign boot plan: `.cps/sovereign_boot.json` — 15 ops, 10 expect assertions (Op 15: sys.now, assert tz=UTC).
Boot proof: `proofs/ns_boot_proof.json` — canonical identity attestation.

## Docker Compose

```bash
# Cold start
docker-compose down --remove-orphans && ./boot.sh

# Rebuild single service
DOCKER_HOST="unix:///Users/${USER}/.docker/run/docker.sock" docker-compose build ns
docker-compose up -d ns
```
