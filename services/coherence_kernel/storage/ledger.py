"""Append-only SQLite WAL ledger with sha256 hash chain."""
from __future__ import annotations
import hashlib, json, sqlite3, threading
from pathlib import Path
from typing import Any

_DB_PATH = Path(__file__).parents[3] / "data" / "coherence_kernel" / "ledger.db"
_MIGRATION = Path(__file__).parent / "migrations" / "0001_init.sql"
_lock = threading.Lock()


def _connect(db_path: Path = _DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(_MIGRATION.read_text())
    conn.commit()
    return conn


_conns: dict[Path, sqlite3.Connection] = {}


def get_conn(db_path: Path = _DB_PATH) -> sqlite3.Connection:
    key = db_path.resolve()
    if key not in _conns:
        _conns[key] = _connect(key)
    return _conns[key]


def close_conn(db_path: Path = _DB_PATH) -> None:
    key = db_path.resolve()
    if key in _conns:
        _conns.pop(key).close()


def _row_hash(table: str, payload_json: str, prev_hash: str) -> str:
    raw = f"{table}:{prev_hash}:{payload_json}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _prev_hash(conn: sqlite3.Connection, table: str) -> str:
    row = conn.execute(f"SELECT row_hash FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
    return row[0] if row else ""


def append(table: str, payload: dict[str, Any], extra_cols: dict[str, Any] | None = None,
           db_path: Path = _DB_PATH) -> str:
    """Append a row; returns row_hash."""
    conn = get_conn(db_path)
    with _lock:
        prev = _prev_hash(conn, table)
        payload_json = json.dumps(payload, sort_keys=True, default=str)
        rh = _row_hash(table, payload_json, prev)
        base = {"payload": payload_json, "prev_hash": prev, "row_hash": rh}
        if extra_cols:
            base.update(extra_cols)
        keys = ", ".join(base.keys())
        placeholders = ", ".join("?" * len(base))
        conn.execute(f"INSERT INTO {table} ({keys}) VALUES ({placeholders})", list(base.values()))
        conn.commit()
        return rh


def verify_chain(table: str, db_path: Path = _DB_PATH) -> bool:
    """Returns True iff hash chain is contiguous from first row to last."""
    conn = get_conn(db_path)
    rows = conn.execute(
        f"SELECT payload, prev_hash, row_hash FROM {table} ORDER BY rowid ASC"
    ).fetchall()
    prev = ""
    for payload_json, stored_prev, stored_hash in rows:
        if stored_prev != prev:
            return False
        expected = _row_hash(table, payload_json, prev)
        if expected != stored_hash:
            return False
        prev = stored_hash
    return True


def append_branch_state(payload: dict, branch_id: str, db_path: Path = _DB_PATH) -> str:
    return append("branch_state", payload, {"id": branch_id}, db_path)


def append_interference_pass(payload: dict, receipt: str, db_path: Path = _DB_PATH) -> str:
    return append("interference_pass", payload, {"receipt": receipt}, db_path)


def append_decoherence_event(payload: dict, branch_id: str, db_path: Path = _DB_PATH) -> str:
    return append("decoherence_event", payload, {"branch_id": branch_id}, db_path)


def append_readiness_score(payload: dict, branch_id: str, score_100: float, db_path: Path = _DB_PATH) -> str:
    return append("readiness_score", payload, {"branch_id": branch_id, "score_100": score_100}, db_path)


def append_promotion(payload: dict, branch_id: str, gate_decision: str, db_path: Path = _DB_PATH) -> str:
    return append("promotion", payload, {"branch_id": branch_id, "gate_decision": gate_decision}, db_path)


def append_reversibility(payload: dict, promotion_id: str, rollback_cost: float, db_path: Path = _DB_PATH) -> str:
    return append("reversibility_ledger", payload, {"promotion_id": promotion_id, "rollback_cost": rollback_cost}, db_path)


def append_receipt(payload: dict, op: str, ref_id: str, db_path: Path = _DB_PATH) -> str:
    return append("receipt", payload, {"op": op, "ref_id": ref_id}, db_path)
