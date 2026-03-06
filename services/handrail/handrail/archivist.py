import sqlite3
import json
import time
import hashlib
import random
import base64
from dataclasses import dataclass
from collections import defaultdict
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

from .migrations import migrate
from .kinds import validate_payload
from .paths import resolve_db_path

def now_us() -> int:
    return int(time.time() * 1_000_000)

class MonotonicULID:
    def __init__(self):
        self.last_ts = 0
        self.last_rand = b"\x00" * 10
    def generate(self) -> str:
        ts = int(time.time() * 1000)
        ts_bytes = ts.to_bytes(6, "big")
        if ts == self.last_ts:
            rand_int = int.from_bytes(self.last_rand, "big") + 1
            rand_bytes = rand_int.to_bytes(10, "big")
        else:
            rand_bytes = random.getrandbits(80).to_bytes(10, "big")
        self.last_ts = ts
        self.last_rand = rand_bytes
        raw = ts_bytes + rand_bytes
        return base64.b32encode(raw).decode("ascii").rstrip("=").lower()

_ulid = MonotonicULID()

@dataclass
class AppendResult:
    accepted: List[str]
    duplicates: List[Dict[str, str]]
    rejected: List[Dict[str, Any]]
    retries: int

class Archivist:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or resolve_db_path()
        self._boot_done = False

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=5)
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA wal_autocheckpoint=1000;")
        return conn

    def boot(self, strict: bool = False) -> Dict[str, Any]:
        migrate(self.db_path)
        report = self.validate_lineage(full=False)
        if not report["valid"]:
            self._quarantine(report)
            if strict:
                raise RuntimeError("Validation failed (strict).")
        self._boot_done = True
        return {"status": "booted", "db_path": self.db_path, "validation": report}

    def doctor(self, integrity_check: bool = False) -> Dict[str, Any]:
        migrate(self.db_path)
        conn = self._conn()
        report: Dict[str, Any] = {"db_path": self.db_path}
        report["wal_mode"] = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        report["page_size"] = conn.execute("PRAGMA page_size;").fetchone()[0]
        report["page_count"] = conn.execute("PRAGMA page_count;").fetchone()[0]
        report["freelist_count"] = conn.execute("PRAGMA freelist_count;").fetchone()[0]
        report["db_bytes_est"] = report["page_size"] * report["page_count"]
        wal = conn.execute("PRAGMA wal_checkpoint(PASSIVE);").fetchone()
        report["wal_checkpoint"] = {"busy": wal[0], "log_pages": wal[1], "checkpointed_pages": wal[2]}
        if integrity_check:
            res = conn.execute("PRAGMA integrity_check;").fetchall()
            report["integrity_check"] = [r[0] for r in res[:50]]
        sessions = conn.execute("SELECT session_id, status, last_activity_us, tenant_id, person_id FROM sessions;").fetchall()
        report["sessions"] = [{"session_id": r[0], "status": r[1], "last_activity_us": r[2], "tenant_id": r[3], "person_id": r[4]} for r in sessions]
        q = conn.execute("SELECT session_id, reason_json, quarantined_at_us FROM quarantined_sessions;").fetchall()
        report["quarantined"] = [{"session_id": r[0], "reason_json": r[1], "quarantined_at_us": r[2]} for r in q]
        conn.close()
        return report

    def append_batch(self, receipts: List[Dict[str, Any]], max_retries: int = 5) -> AppendResult:
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for rec in receipts:
            validate_payload(rec["kind"], rec["payload_json"])
            grouped[rec["session_id"]].append(rec)

        accepted: List[str] = []
        duplicates: List[Dict[str, str]] = []
        rejected: List[Dict[str, Any]] = []

        retry = 0
        while retry < max_retries:
            conn = self._conn()
            cur = conn.cursor()
            try:
                conn.execute("BEGIN IMMEDIATE;")

                for sid, group in grouped.items():
                    tenant = group[0].get("tenant_id", "default")
                    person = group[0].get("person_id")
                    actor = group[0].get("actor_id", "unknown")

                    row = cur.execute("SELECT status, tenant_id, person_id FROM sessions WHERE session_id=?;", (sid,)).fetchone()
                    if row is None:
                        cur.execute(
                            "INSERT INTO sessions(session_id,status,created_at_us,last_activity_us,actor_id,tenant_id,person_id) VALUES (?,?,?,?,?,?,?);",
                            (sid, "open", now_us(), now_us(), actor, tenant, person),
                        )
                    else:
                        status, db_tenant, _db_person = row
                        if status != "open":
                            rejected.append({"session_id": sid, "reason": "session_not_open"})
                            continue
                        if db_tenant != tenant:
                            rejected.append({"session_id": sid, "reason": "tenant_mismatch", "tenant": tenant, "db_tenant": db_tenant})
                            continue

                    ikeys = [r.get("idempotency_key") for r in group if r.get("idempotency_key")]
                    dup_map: Dict[str, str] = {}
                    if ikeys:
                        placeholders = ",".join(["?"] * len(ikeys))
                        rows = cur.execute(
                            f"SELECT idempotency_key, receipt_id FROM receipts WHERE session_id=? AND idempotency_key IN ({placeholders});",
                            (sid, *ikeys),
                        ).fetchall()
                        dup_map = {r[0]: r[1] for r in rows}

                    new_group = []
                    for r in group:
                        ik = r.get("idempotency_key")
                        if ik and ik in dup_map:
                            duplicates.append({"session_id": sid, "idempotency_key": ik, "receipt_id": dup_map[ik]})
                        else:
                            new_group.append(r)
                    group = new_group
                    if not group:
                        continue

                    n = len(group)
                    row = cur.execute("SELECT next_seq FROM session_counters WHERE session_id=?;", (sid,)).fetchone()
                    if row:
                        start_seq = row[0]
                        cur.execute("UPDATE session_counters SET next_seq = next_seq + ? WHERE session_id=?;", (n, sid))
                    else:
                        start_seq = 1
                        cur.execute("INSERT INTO session_counters(session_id,next_seq) VALUES(?,?);", (sid, n + 1))

                    prev_h = None
                    if start_seq > 1:
                        r = cur.execute("SELECT hash FROM receipts WHERE session_id=? AND session_seq=?;", (sid, start_seq - 1)).fetchone()
                        prev_h = r[0] if r else None

                    insert_rows: List[Tuple[Any, ...]] = []
                    for i, r in enumerate(group):
                        seq = start_seq + i
                        receipt_id = r.get("receipt_id") or _ulid.generate()
                        ts_us = r.get("ts_us") or now_us()
                        kind = r["kind"]
                        payload_json = json.dumps(r["payload_json"], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                        parent = r.get("parent_receipt_id")
                        prev_hash = r.get("prev_hash", prev_h)
                        # Genesis rule: represent "no previous" as empty string, never NULL.
                        if prev_hash is None:
                            prev_hash = ""

                        stable = {
                            "receipt_id": receipt_id,
                            "session_seq": seq,
                            "ts_us": ts_us,
                            "actor_id": actor,
                            "tenant_id": tenant,
                            "person_id": person,
                            "session_id": sid,
                            "kind": kind,
                            "payload_json": payload_json,
                            "parent_receipt_id": parent,
                            "prev_hash": prev_hash,
                        }
                        canonical = json.dumps(stable, sort_keys=True, separators=(",", ":")).encode("utf-8")
                        h = hashlib.sha256(canonical).hexdigest()
                        committed_at = datetime.utcnow().isoformat() + "Z"

                        insert_rows.append((
                            receipt_id, seq, ts_us, actor, tenant, person, sid, kind, payload_json,
                            parent, prev_hash, h, r.get("idempotency_key"), committed_at
                        ))
                        prev_h = h

                    cur.executemany(
                        """
                        INSERT INTO receipts(
                            receipt_id, session_seq, ts_us, actor_id, tenant_id, person_id, session_id, kind, payload_json,
                            parent_receipt_id, prev_hash, hash, idempotency_key, committed_at
                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?);
                        """,
                        insert_rows,
                    )
                    accepted.extend([row[0] for row in insert_rows])
                    cur.execute("UPDATE sessions SET last_activity_us=? WHERE session_id=?;", (now_us(), sid))

                conn.commit()
                conn.close()
                break
            except sqlite3.OperationalError as e:
                conn.rollback()
                conn.close()
                if "busy" in str(e).lower():
                    retry += 1
                    time.sleep(0.1 * retry)
                    continue
                raise
            except sqlite3.IntegrityError as e:
                conn.rollback()
                conn.close()
                rejected.append({"reason": "integrity_error", "detail": str(e)})
                break

        for sid in grouped.keys():
            v = self.validate_session(sid, full=False)
            if not v["valid"]:
                self._quarantine(v)

        return AppendResult(accepted=accepted, duplicates=duplicates, rejected=rejected, retries=retry)

    def _row_to_dict(self, row: Tuple[Any, ...]) -> Dict[str, Any]:
        return {
            "receipt_id": row[0], "session_seq": row[1], "ts_us": row[2], "actor_id": row[3],
            "tenant_id": row[4], "person_id": row[5], "session_id": row[6],
            "kind": row[7], "payload_json": json.loads(row[8]),
            "parent_receipt_id": row[9], "prev_hash": row[10], "hash": row[11],
            "idempotency_key": row[12], "committed_at": row[13],
        }

    def read(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT receipt_id, session_seq, ts_us, actor_id, tenant_id, person_id, session_id, kind, payload_json, parent_receipt_id, prev_hash, hash, idempotency_key, committed_at "
            "FROM receipts WHERE session_id=? ORDER BY session_seq DESC LIMIT ?;",
            (session_id, limit),
        ).fetchall()
        conn.close()
        return [self._row_to_dict(r) for r in rows]

    def latest(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Return the newest receipt (highest session_seq) for a session."""
        conn = self._get_conn()
        cur = conn.cursor()
        row = cur.execute(
            "SELECT receipt_id, session_seq, ts_us, actor_id, tenant_id, person_id, session_id, kind, payload_json, parent_receipt_id, prev_hash, hash, idempotency_key, committed_at "
            "FROM receipts WHERE session_id=? ORDER BY session_seq DESC LIMIT 1;",
            (session_id,),
        ).fetchone()
        conn.close()
        return self._row_to_dict(row) if row else None

    def validate_lineage(self, full: bool = False) -> Dict[str, Any]:
        conn = self._conn()
        sids = [r[0] for r in conn.execute("SELECT session_id FROM sessions WHERE status != 'quarantined';").fetchall()]
        conn.close()
        report = {"valid": True, "errors": [], "checked": 0}
        for sid in sids:
            r = self.validate_session(sid, full=full)
            report["checked"] += r["checked"]
            if not r["valid"]:
                report["valid"] = False
                report["errors"].extend(r["errors"])
        return report

    def validate_session(self, session_id: str, full: bool = False) -> Dict[str, Any]:
        conn = self._conn()
        cur = conn.cursor()

        if full:
            cur.execute("INSERT OR REPLACE INTO validation_state(session_id,last_validated_seq,last_validated_hash,validated_at_us) VALUES(?,?,?,?);",
                        (session_id, 0, "", 0))
            conn.commit()

        row = cur.execute("SELECT last_validated_seq, last_validated_hash FROM validation_state WHERE session_id=?;", (session_id,)).fetchone()
        start_seq = row[0] if row else 0
        # Genesis rule: seq=1 must have prev_hash == "".
        # Treat missing validation_state as "" (not None) to avoid false chain_break.
        expected_prev = (row[1] if row else "")

        rows = cur.execute(
            "SELECT receipt_id, session_seq, ts_us, actor_id, tenant_id, person_id, session_id, kind, payload_json, parent_receipt_id, prev_hash, hash, idempotency_key, committed_at "
            "FROM receipts WHERE session_id=? AND session_seq > ? ORDER BY session_seq ASC;",
            (session_id, start_seq),
        ).fetchall()

        report = {"valid": True, "errors": [], "checked": 0, "session_id": session_id}

        prev_h = expected_prev
        prev_seq = start_seq
        prev_ts = None

        delta: Dict[str, Dict[str, Any]] = {}
        out_parent_cache: Dict[str, Tuple[int, str]] = {}
        action_state: Dict[str, str] = {}

        for row in rows:
            report["checked"] += 1
            d = self._row_to_dict(row)
            delta[d["receipt_id"]] = d

            payload_json = json.dumps(d["payload_json"], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            stable = {
                "receipt_id": d["receipt_id"],
                "session_seq": d["session_seq"],
                "ts_us": d["ts_us"],
                "actor_id": d["actor_id"],
                "tenant_id": d["tenant_id"],
                "person_id": d["person_id"],
                "session_id": d["session_id"],
                "kind": d["kind"],
                "payload_json": payload_json,
                "parent_receipt_id": d["parent_receipt_id"],
                "prev_hash": d["prev_hash"],
            }
            canonical = json.dumps(stable, sort_keys=True, separators=(",", ":")).encode("utf-8")
            computed = hashlib.sha256(canonical).hexdigest()
            if computed != d["hash"]:
                report["errors"].append({"code": "hash_mismatch", "seq": d["session_seq"], "receipt_id": d["receipt_id"]})

            if d["session_seq"] != prev_seq + 1:
                report["errors"].append({"code": "seq_gap", "expected": prev_seq + 1, "got": d["session_seq"]})
            if (d["prev_hash"] or "") != (prev_h or ""):
                report["errors"].append({"code": "chain_break", "seq": d["session_seq"]})
            if prev_ts is not None and d["ts_us"] < prev_ts:
                report["errors"].append({"code": "ts_non_monotonic", "seq": d["session_seq"]})

            if d["kind"] == "identity_linked":
                pid = d["payload_json"].get("person_id")
                exists = cur.execute("SELECT 1 FROM persons WHERE person_id=?;", (pid,)).fetchone()
                if not exists:
                    report["errors"].append({"code": "unknown_person_id", "seq": d["session_seq"], "person_id": pid})

            if "action_id" in d["payload_json"]:
                aid = d["payload_json"]["action_id"]
                k = d["kind"]
                prev_state = action_state.get(aid)
                def err(code):
                    report["errors"].append({"code": code, "seq": d["session_seq"], "action_id": aid})
                if k == "action_requested":
                    if prev_state is not None:
                        err("action_duplicate_request")
                    action_state[aid] = "requested"
                elif k == "action_approved":
                    if prev_state != "requested":
                        err("action_bad_transition")
                    action_state[aid] = "approved"
                elif k == "action_started":
                    if prev_state not in ("approved", "requested"):
                        err("action_bad_transition")
                    action_state[aid] = "started"
                elif k in ("action_completed", "action_failed"):
                    if prev_state != "started":
                        err("action_bad_transition")
                    action_state[aid] = "terminal"
                elif k == "action_canceled":
                    action_state[aid] = "terminal"

            prev_h = d["hash"]
            prev_seq = d["session_seq"]
            prev_ts = d["ts_us"]

        for rid, d in delta.items():
            parent = d["parent_receipt_id"]
            if not parent:
                continue
            if parent in delta:
                if delta[parent]["session_seq"] >= d["session_seq"]:
                    report["errors"].append({"code": "invalid_parent_order", "receipt_id": rid})
            else:
                if parent not in out_parent_cache:
                    prow = cur.execute("SELECT session_seq, session_id FROM receipts WHERE receipt_id=?;", (parent,)).fetchone()
                    out_parent_cache[parent] = prow if prow else (-1, "")
                pseq, psid = out_parent_cache[parent]
                if psid != session_id or pseq < 0 or pseq >= d["session_seq"]:
                    report["errors"].append({"code": "invalid_parent", "receipt_id": rid, "parent": parent})

        if report["errors"]:
            report["valid"] = False
        else:
            # If a session is now valid, clear any prior quarantine marker.
            cur.execute("UPDATE sessions SET status='open' WHERE session_id=? AND status='quarantined';", (session_id,))
            cur.execute("DELETE FROM quarantined_sessions WHERE session_id=?;", (session_id,))
            cur.execute(
                "INSERT OR REPLACE INTO validation_state(session_id,last_validated_seq,last_validated_hash,validated_at_us) VALUES(?,?,?,?);",
                (session_id, prev_seq, prev_h or "", now_us()),
            )
            conn.commit()

        conn.close()
        return report

    def _quarantine(self, report: Dict[str, Any]) -> None:
        conn = self._conn()
        cur = conn.cursor()
        errs = report.get("errors", [])
        sid = report.get("session_id")
        if sid:
            sids = {sid}
        else:
            sids = {e.get("session_id") for e in errs if e.get("session_id")}
            sids = {s for s in sids if s}
        for sid in sids:
            cur.execute("UPDATE sessions SET status='quarantined' WHERE session_id=?;", (sid,))
            cur.execute(
                "INSERT OR REPLACE INTO quarantined_sessions(session_id,reason_json,quarantined_at_us) VALUES(?,?,?);",
                (sid, json.dumps(errs, ensure_ascii=False), now_us()),
            )
        conn.commit()
        conn.close()

    def repair_fork(self, session_id: str) -> Dict[str, Any]:
        conn = self._conn()
        cur = conn.cursor()
        row = cur.execute("SELECT last_validated_seq FROM validation_state WHERE session_id=?;", (session_id,)).fetchone()
        valid_seq = row[0] if row else 0
        if valid_seq <= 0:
            conn.close()
            return {"ok": False, "reason": "no_valid_prefix"}

        new_sid = f"{session_id}_fork_{_ulid.generate()}"

        srow = cur.execute("SELECT actor_id, tenant_id, person_id, last_activity_us FROM sessions WHERE session_id=?;", (session_id,)).fetchone()
        if not srow:
            conn.close()
            return {"ok": False, "reason": "session_not_found"}

        actor, tenant, person, last_act = srow
        cur.execute(
            "INSERT INTO sessions(session_id,status,created_at_us,last_activity_us,actor_id,tenant_id,person_id) VALUES(?,?,?,?,?,?,?);",
            (new_sid, "open", now_us(), last_act, actor, tenant, person),
        )
        cur.execute("INSERT OR REPLACE INTO session_counters(session_id,next_seq) VALUES(?,?);", (new_sid, valid_seq + 1))

        rows = cur.execute(
            "SELECT receipt_id, session_seq, ts_us, actor_id, tenant_id, person_id, session_id, kind, payload_json, parent_receipt_id, prev_hash, hash, idempotency_key, committed_at "
            "FROM receipts WHERE session_id=? AND session_seq <= ? ORDER BY session_seq ASC;",
            (session_id, valid_seq),
        ).fetchall()

        id_map: Dict[str, str] = {row[0]: _ulid.generate() for row in rows}

        prev_h = None
        inserts = []
        for row in rows:
            d = self._row_to_dict(row)
            new_id = id_map[d["receipt_id"]]
            old_parent = d["parent_receipt_id"]
            new_parent = id_map.get(old_parent) if old_parent else None

            payload_json = json.dumps(d["payload_json"], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            stable = {
                "receipt_id": new_id,
                "session_seq": d["session_seq"],
                "ts_us": d["ts_us"],
                "actor_id": actor,
                "tenant_id": tenant,
                "person_id": person,
                "session_id": new_sid,
                "kind": d["kind"],
                "payload_json": payload_json,
                "parent_receipt_id": new_parent,
                "prev_hash": prev_h,
            }
            canonical = json.dumps(stable, sort_keys=True, separators=(",", ":")).encode("utf-8")
            h = hashlib.sha256(canonical).hexdigest()
            committed_at = datetime.utcnow().isoformat() + "Z"

            inserts.append((
                new_id, d["session_seq"], d["ts_us"], actor, tenant, person, new_sid, d["kind"], payload_json,
                new_parent, prev_h, h, d["idempotency_key"], committed_at
            ))
            prev_h = h

        cur.executemany(
            """
            INSERT INTO receipts(
                receipt_id, session_seq, ts_us, actor_id, tenant_id, person_id, session_id, kind, payload_json,
                parent_receipt_id, prev_hash, hash, idempotency_key, committed_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?);
            """,
            inserts,
        )

        conn.commit()
        conn.close()

        # marker + close old + validate
        self.append_batch([{
            "actor_id": actor,
            "tenant_id": tenant,
            "person_id": person,
            "session_id": new_sid,
            "kind": "repair_applied",
            "payload_json": {"old_session_id": session_id, "reason": "fork_repair"},
            "idempotency_key": f"repair:{session_id}",
        }])

        conn = self._conn()
        conn.execute("UPDATE sessions SET status='closed' WHERE session_id=?;", (session_id,))
        conn.commit()
        conn.close()

        v = self.validate_session(new_sid, full=True)
        return {"ok": v["valid"], "new_session_id": new_sid, "validation": v}
