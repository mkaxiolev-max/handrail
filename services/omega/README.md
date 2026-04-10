# Omega

Omega is a bounded simulation service that runs inside the NS repository.

Current scope in this phase:

- FastAPI service with bounded branch simulation
- DB-backed run and branch persistence
- Receipt-backed run creation using the shared NS receipt rail
- Founder-safe Alexandria-compatible summary atom writes
- No Canon writes
- No Handrail execution
- All outputs remain provisional by design

Current API:

- `GET /healthz`
- `GET /omega/healthz`
- `POST /omega/simulate`
- `GET /omega/runs`
- `GET /omega/runs/{run_id}`
- `GET /omega/runs/{run_id}/branches`

Governance boundaries:

- Simulation outputs are non-canonical.
- Omega does not write Canon.
- Omega does not trigger Handrail execution.
- Every persisted run carries receipt linkage.
