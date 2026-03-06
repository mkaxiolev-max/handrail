# Handrail architecture (final)

## Core invariants
- Append-only receipts
- Per-session strict ordering: `session_seq` from `session_counters`
- Integrity: `hash = sha256(canonical(stable_fields))` with `prev_hash` chaining
- Causality: optional `parent_receipt_id` validated as earlier in same session
- Delta validation: validate from `validation_state.last_validated_seq`
- Quarantine on validation failures; boot continues unless strict
- Repair: fork session by copying validated prefix, **remapping parent IDs**, rebuilding hashes

## Identity linking
- `identity_linked` enforced at DB-level: one per session via partial unique index
- Validation requires person_id exists in `persons`

## LLM ↔ Terminal mediation
Handrail is the durable rail and policy boundary:
- LLM emits plan -> NS converts to terminal actions -> Handrail stores proof/results
- Replay never re-executes terminal actions
