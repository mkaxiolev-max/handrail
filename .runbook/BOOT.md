# Boot Runbook

## Fast path
./scripts/boot/boot_ez.sh

Use when Handrail is already up and you only want to restart NS + Continuum.

## Recovery path
./scripts/boot/reset_clean.sh

Use when Docker was restarted, the stack is down, or state is questionable.

## Status
./scripts/boot/status.sh

## Snapshot
./scripts/boot/snapshot.sh

## Acceptance
A run is good when:
- handrail /healthz returns 200
- ns /healthz returns 200
- continuum /state returns 200
- ns healthz shows storage.external_ssd=true
- run bundle exists under /Volumes/NSExternal/.run/boot/

## Notes
- Continuum may briefly show "health: starting" in docker compose ps after boot even when /state is already healthy.
- Prefer endpoint truth over transient compose health text.
