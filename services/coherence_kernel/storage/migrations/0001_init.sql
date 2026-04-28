-- Coherence Kernel — append-only ledger schema
-- PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; set at connection time.

CREATE TABLE IF NOT EXISTS branch_state (
    rowid       INTEGER PRIMARY KEY AUTOINCREMENT,
    id          TEXT    NOT NULL,
    payload     TEXT    NOT NULL,
    prev_hash   TEXT    NOT NULL DEFAULT '',
    row_hash    TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS interference_pass (
    rowid       INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt     TEXT    NOT NULL,
    payload     TEXT    NOT NULL,
    prev_hash   TEXT    NOT NULL DEFAULT '',
    row_hash    TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS decoherence_event (
    rowid       INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id   TEXT    NOT NULL,
    payload     TEXT    NOT NULL,
    prev_hash   TEXT    NOT NULL DEFAULT '',
    row_hash    TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS readiness_score (
    rowid       INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id   TEXT    NOT NULL,
    score_100   REAL    NOT NULL,
    payload     TEXT    NOT NULL,
    prev_hash   TEXT    NOT NULL DEFAULT '',
    row_hash    TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS promotion (
    rowid       INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id   TEXT    NOT NULL,
    gate_decision TEXT  NOT NULL,
    payload     TEXT    NOT NULL,
    prev_hash   TEXT    NOT NULL DEFAULT '',
    row_hash    TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS reversibility_ledger (
    rowid       INTEGER PRIMARY KEY AUTOINCREMENT,
    promotion_id TEXT   NOT NULL,
    rollback_cost REAL  NOT NULL,
    payload     TEXT    NOT NULL,
    prev_hash   TEXT    NOT NULL DEFAULT '',
    row_hash    TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS receipt (
    rowid       INTEGER PRIMARY KEY AUTOINCREMENT,
    op          TEXT    NOT NULL,
    ref_id      TEXT    NOT NULL,
    payload     TEXT    NOT NULL,
    prev_hash   TEXT    NOT NULL DEFAULT '',
    row_hash    TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- Deny UPDATE/DELETE on every table via triggers
CREATE TRIGGER IF NOT EXISTS deny_update_branch_state        BEFORE UPDATE ON branch_state        BEGIN SELECT RAISE(ABORT,'append-only: UPDATE denied'); END;
CREATE TRIGGER IF NOT EXISTS deny_delete_branch_state        BEFORE DELETE ON branch_state        BEGIN SELECT RAISE(ABORT,'append-only: DELETE denied'); END;
CREATE TRIGGER IF NOT EXISTS deny_update_interference_pass   BEFORE UPDATE ON interference_pass   BEGIN SELECT RAISE(ABORT,'append-only: UPDATE denied'); END;
CREATE TRIGGER IF NOT EXISTS deny_delete_interference_pass   BEFORE DELETE ON interference_pass   BEGIN SELECT RAISE(ABORT,'append-only: DELETE denied'); END;
CREATE TRIGGER IF NOT EXISTS deny_update_decoherence_event   BEFORE UPDATE ON decoherence_event   BEGIN SELECT RAISE(ABORT,'append-only: UPDATE denied'); END;
CREATE TRIGGER IF NOT EXISTS deny_delete_decoherence_event   BEFORE DELETE ON decoherence_event   BEGIN SELECT RAISE(ABORT,'append-only: DELETE denied'); END;
CREATE TRIGGER IF NOT EXISTS deny_update_readiness_score     BEFORE UPDATE ON readiness_score     BEGIN SELECT RAISE(ABORT,'append-only: UPDATE denied'); END;
CREATE TRIGGER IF NOT EXISTS deny_delete_readiness_score     BEFORE DELETE ON readiness_score     BEGIN SELECT RAISE(ABORT,'append-only: DELETE denied'); END;
CREATE TRIGGER IF NOT EXISTS deny_update_promotion           BEFORE UPDATE ON promotion           BEGIN SELECT RAISE(ABORT,'append-only: UPDATE denied'); END;
CREATE TRIGGER IF NOT EXISTS deny_delete_promotion           BEFORE DELETE ON promotion           BEGIN SELECT RAISE(ABORT,'append-only: DELETE denied'); END;
CREATE TRIGGER IF NOT EXISTS deny_update_reversibility_ledger BEFORE UPDATE ON reversibility_ledger BEGIN SELECT RAISE(ABORT,'append-only: UPDATE denied'); END;
CREATE TRIGGER IF NOT EXISTS deny_delete_reversibility_ledger BEFORE DELETE ON reversibility_ledger BEGIN SELECT RAISE(ABORT,'append-only: DELETE denied'); END;
CREATE TRIGGER IF NOT EXISTS deny_update_receipt             BEFORE UPDATE ON receipt             BEGIN SELECT RAISE(ABORT,'append-only: UPDATE denied'); END;
CREATE TRIGGER IF NOT EXISTS deny_delete_receipt             BEFORE DELETE ON receipt             BEGIN SELECT RAISE(ABORT,'append-only: DELETE denied'); END;
