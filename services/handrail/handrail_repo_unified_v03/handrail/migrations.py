import sqlite3

SCHEMA_VERSION = 5  # v5: identity unique index + persons table + validation_state

def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (name,))
    return cur.fetchone() is not None

def index_exists(conn: sqlite3.Connection, name: str) -> bool:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND name=?;", (name,))
    return cur.fetchone() is not None

def migrate(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA wal_autocheckpoint=1000;")

    if not table_exists(conn, "schema_migrations"):
        conn.execute("""
        CREATE TABLE schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

    cur = conn.execute("SELECT MAX(version) FROM schema_migrations;")
    current = cur.fetchone()[0] or 0

    if current < 1:
        conn.execute("""
        CREATE TABLE receipts (
            receipt_id TEXT PRIMARY KEY,
            session_seq INTEGER NOT NULL,
            ts_us INTEGER NOT NULL,
            actor_id TEXT NOT NULL,
            tenant_id TEXT NOT NULL DEFAULT "default",
            person_id TEXT,
            session_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            parent_receipt_id TEXT,
            prev_hash TEXT,
            hash TEXT NOT NULL,
            idempotency_key TEXT,
            committed_at TEXT,
            UNIQUE(session_id, session_seq),
            UNIQUE(session_id, idempotency_key)
        );
        """)
        conn.execute("CREATE INDEX idx_session_ts ON receipts(session_id, ts_us);")
        conn.execute("CREATE INDEX idx_kind_ts ON receipts(kind, ts_us);")
        conn.execute("CREATE INDEX idx_tenant_session ON receipts(tenant_id, session_id, session_seq);")

        conn.execute("""
        CREATE TABLE session_counters (
            session_id TEXT PRIMARY KEY,
            next_seq INTEGER NOT NULL DEFAULT 1
        );
        """)

        conn.execute("""
        CREATE TABLE sessions (
            session_id TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'open',
            created_at_us INTEGER NOT NULL,
            last_activity_us INTEGER NOT NULL,
            actor_id TEXT NOT NULL,
            tenant_id TEXT NOT NULL DEFAULT "default",
            person_id TEXT
        );
        """)

        conn.execute("""
        CREATE TABLE snapshots (
            session_id TEXT PRIMARY KEY,
            ts_us INTEGER NOT NULL,
            state_json TEXT NOT NULL,
            receipt_id_at_snapshot TEXT NOT NULL,
            session_seq_at_snapshot INTEGER NOT NULL
        );
        """)

        conn.execute("""
        CREATE TABLE validation_state (
            session_id TEXT PRIMARY KEY,
            last_validated_seq INTEGER NOT NULL DEFAULT 0,
            last_validated_hash TEXT NOT NULL DEFAULT "",
            validated_at_us INTEGER NOT NULL DEFAULT 0
        );
        """)

        conn.execute("""
        CREATE TABLE quarantined_sessions (
            session_id TEXT PRIMARY KEY,
            reason_json TEXT NOT NULL,
            quarantined_at_us INTEGER NOT NULL
        );
        """)

        conn.execute("INSERT INTO schema_migrations(version) VALUES (1);")

    if not table_exists(conn, "persons"):
        conn.execute("""
        CREATE TABLE persons (
            person_id TEXT PRIMARY KEY,
            created_at_us INTEGER NOT NULL,
            metadata_json TEXT NOT NULL DEFAULT "{}"
        );
        """)

    if not index_exists(conn, "idx_single_identity_link"):
        conn.execute("""
        CREATE UNIQUE INDEX idx_single_identity_link
        ON receipts(session_id)
        WHERE kind = 'identity_linked';
        """)

    conn.execute("INSERT OR REPLACE INTO schema_migrations(version) VALUES (?);", (SCHEMA_VERSION,))
    conn.commit()
    conn.close()
