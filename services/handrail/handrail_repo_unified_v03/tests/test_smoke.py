import os
import sqlite3

# Allow `python tests/test_smoke.py` without needing PYTHONPATH.
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from handrail.archivist import Archivist

def test_smoke_quarantine_and_repair(tmp_path):
    db = tmp_path / "handrail.db"
    os.environ["HANDRAIL_DB"] = str(db)
    arch = Archivist()
    arch.boot()

    arch.append_batch([
        {"actor_id":"t","session_id":"good","kind":"session_start","payload_json":{"context":"good"}, "idempotency_key":"start"},
        {"actor_id":"t","session_id":"corrupt","kind":"session_start","payload_json":{"context":"bad"}, "idempotency_key":"start"},
    ])

    conn = sqlite3.connect(str(db))
    conn.execute("UPDATE receipts SET hash='bad_hash' WHERE session_id='corrupt' AND session_seq=1;")
    conn.commit()
    conn.close()

    v = arch.validate_session("corrupt", full=True)
    assert not v["valid"]
    arch._quarantine(v)

    rep = arch.repair_fork("corrupt")
    assert rep["ok"]
