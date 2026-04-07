# NS∞ Founder Operations Manual

## Quick Start

```bash
cd ~/axiolev_runtime && docker compose up -d
curl http://127.0.0.1:9000/healthz
```

## Services

| Service      | Port | Purpose                        |
|-------------|------|-------------------------------|
| ns_core      | 9000 | Violet interface, feed, boot  |
| alexandria   | 9001 | Memory, parse, atoms, graph   |
| model_router | 9002 | LLM routing                   |
| violet       | 9003 | Voice + chat services         |
| canon        | 9004 | Canonical state               |
| integrity    | 9005 | Receipt chain + audit         |

## Key Endpoints

```bash
# Health
curl http://127.0.0.1:9000/healthz

# Feed briefing
curl http://127.0.0.1:9000/feed/briefing

# Violet status
curl http://127.0.0.1:9000/violet/status

# Integrity chain
curl http://127.0.0.1:9005/integrity/chain

# Verify receipts
curl -X POST http://127.0.0.1:9005/integrity/verify

# Build feed
curl -X POST http://127.0.0.1:9000/feed/build
```

## Founder Modes

- **Strategic** — discuss, review, plan
- **Command** — execute programs, ratify decisions
- **Monitoring** — watch system state
- **Reflective** — review past states

## Constitutional Boundaries (HARD)

- Dignity Kernel never-events: cannot be overridden
- Handrail gates: all actions go through kernel
- Receipt immutability: append-only, no edits
- Violet: single interface, multiple modes

## Logs

```bash
docker compose logs -f ns_core
docker compose logs -f integrity
docker compose logs -f alexandria
```

## Shutdown

```bash
docker compose down
```
