# NS∞ Founder Cockpit (MAX)
Native macOS founder surface. Truth machine. Command center. Receipt viewer.

## Required services (boot order matters)

1. **NCOM dashboard on :9020** (host process — full Python access to coherence kernel)
2. **Docker stack** — `ns_core` on :9000, `continuum` on :8788, `ris` on :8014
3. **Mac Adapter on :8765** (host process — osascript bridge)

> **Critical:** If NCOM is not running on :9020, every `/query` to NS Core returns 503.
> The `ns_core` Docker container reaches NCOM via `host.docker.internal:9020`.
> This is intentional — the coherence kernel Python modules live on the host so
> `ns_core` stays a lightweight container.

## Boot (single command)

```bash
bash ~/axiolev_runtime/resume_ns.sh
```

`resume_ns.sh` already wires:
- `docker compose up -d` (handrail, ns_core, ns, continuum, ris)
- `scripts/run_coherence_dashboard.sh` → NCOM on :9020
- Mac Adapter (if script is present)

## Build

```bash
cd ~/axiolev_runtime/apps/founder_cockpit_mac
bash build_founder_cockpit.sh
```

Output: `dist/mac/NSFounderCockpit.app`

## Run

```bash
open dist/mac/NSFounderCockpit.app          # GUI — requires NS∞ stack running
.build/arm64-apple-macosx/release/NSFounderCockpit  # CLI fallback
```

## Acceptance

```bash
bash run_acceptance.sh
```

Checks 6 live endpoints, IMO gate verb, ledger integrity, and runs 17 XCTests.

## Architecture

```
Cockpit (SwiftUI)  ──POST /query──►  NS Core :9000
                                          │
                                     HTTP to host
                                          │
                                    NCOM :9020 ──► IMO Gate (propose → adjudicate)
                                                ──► Branch Registry
                                                ──► Decoherence Aggregator
                                                ──► Readiness Score

Cockpit  ──────────────────────────►  Handrail :8011  (CPS execution)
Cockpit  ──────────────────────────►  Mac Adapter :8765  (read-only Mac surface)
Cockpit  ──────────────────────────►  RIS :8014  (reality ingestion lanes)
Cockpit  ──────────────────────────►  Continuum :8788  (event store / tier state)
```

## 9-Dimension Score Rubric

| Dim | Dimension | Full score condition |
|-----|-----------|---------------------|
| D1 | Endpoint Availability | All 6 core services up |
| D2 | IMO Gate Query Routing | POST /query returns valid verb |
| D3 | NCOM Dashboard :9020 | /ncom/healthz responds |
| D4 | Canon Panel | /canon reachable + records present |
| D5 | Contradiction Tracking | pressure_score ≤ 1.0 |
| D6 | Memory Atoms/Molecules | /memory/atoms populated |
| D7 | Storytime Narration | rule field non-empty |
| D8 | Mac Adapter Bridge :8765 | /healthz responds |
| D9 | Receipt/Ledger Integrity | all_chains_valid = true |

## Author

Mike Kenworthy / AXIOLEV Holdings LLC. Sole-author IP.
Branch: `integration/founder-cockpit-mac-MAX-20260428`
Tag: `founder-cockpit-MAX-v1`
