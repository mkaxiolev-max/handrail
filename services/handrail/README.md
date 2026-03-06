# Handrail (v4.2-final) — Local-first persistence rail + LLM↔Terminal mediator

Handrail is an **append-only receipt ledger** for NS∞:
- Durable event capture (SQLite WAL)
- Deterministic ordering (`session_seq`)
- Integrity (hash chain)
- Causality (optional `parent_receipt_id`)
- Incremental validation (delta from last_validated_seq)
- Quarantine + fork repair (self-healing)
- Replay (pure reducer model)
- Optional: Menu Bar app + local inspector UI

## Quickstart (CLI)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m handrail.cli doctor
python -m handrail.cli boot
```

## Where the DB lives
Default:
`~/Library/Application Support/Handrail/handrail.db`

Override:
`HANDRAIL_DB=/path/to/handrail.db python -m handrail.cli doctor`

## Optional UI
### Inspector (FastAPI)
```bash
pip install -r requirements-ui.txt
python -m inspector.app
# open http://127.0.0.1:8000
```

### Menu Bar App (rumps)
```bash
pip install -r requirements-macapp.txt
python mac_app/app.py
```

## Tests
```bash
pip install -r requirements-dev.txt
pytest -q

# Or run the smoke test directly (no pytest needed)
python tests/test_smoke.py
```
