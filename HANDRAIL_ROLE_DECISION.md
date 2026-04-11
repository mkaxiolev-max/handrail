# HANDRAIL ROLE DECISION
Generated: Fri Apr 10 19:01:47 PDT 2026

## Verdict: Option A

**Option A: Handrail is in the current runtime topology.**

## Evidence
- In docker-compose: True
- Handrail dirs: ['handrail_cli.py', 'handrail-cli', 'handrail-core']
- Port 8011 live: False
- ns_core handrail refs: 2

## Current Handrail Role (Option B)
Handrail is the CPS execution control plane product. It runs as a separate service
when active. NS Infinity currently routes all execution directly through ns_core.
This is not degradation — it is the current architectural truth.

## Merge Path
To make Handrail the authoritative actuator spine:
1. Add handrail service to docker-compose.yml at :8011
2. ns_core routes execution calls → handrail
3. Handrail receipts fed back to Alexandria
4. Ring 5 Stripe gates activated

## Current Status
PARALLEL_PRODUCT — not degraded, not removed, not required for current operation.
