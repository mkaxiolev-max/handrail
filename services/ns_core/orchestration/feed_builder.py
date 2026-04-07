"""
Feed builder — queries system state from postgres and generates typed feed cards.
Writes receipts to integrity service for every feed_generated event.
"""

import os
import json
import hashlib
import datetime
import psycopg2

DB_URL = os.environ.get("DATABASE_URL", "postgresql://ns:ns_secure_pwd@postgres:5432/ns")


def _conn():
    return psycopg2.connect(DB_URL)


def _query_system_state(cur) -> dict:
    cur.execute("SELECT COUNT(*) FROM source_items")
    files_scanned = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM atoms")
    atoms_created = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM edges")
    edges_created = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM atoms WHERE type = 'arc'")
    founder_arcs = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM atoms WHERE type = 'open_loop'")
    open_loops = cur.fetchone()[0]

    cur.execute(
        "SELECT id::text, content FROM atoms WHERE type = 'arc' ORDER BY created_at DESC LIMIT 10"
    )
    arc_rows = cur.fetchall()
    arc_list = [{"id": r[0], "content": r[1]} for r in arc_rows]

    cur.execute(
        "SELECT id::text, content FROM atoms WHERE type = 'open_loop' ORDER BY created_at DESC LIMIT 10"
    )
    loop_rows = cur.fetchall()
    loop_list = [{"id": r[0], "content": r[1]} for r in loop_rows]

    return {
        "files_scanned": files_scanned,
        "atoms_created": atoms_created,
        "edges_created": edges_created,
        "founder_arcs": founder_arcs,
        "open_loops": open_loops,
        "arc_list": arc_list,
        "loop_list": loop_list,
    }


def _build_cards(state: dict) -> list:
    ts = datetime.datetime.utcnow().isoformat()
    cards = [
        {
            "type": "system_stat",
            "payload": {
                "label": f"{state['files_scanned']} files scanned",
                "metric": "files_scanned",
                "value": state["files_scanned"],
                "ts": ts,
            },
        },
        {
            "type": "system_stat",
            "payload": {
                "label": f"{state['atoms_created']} atoms created",
                "metric": "atoms_created",
                "value": state["atoms_created"],
                "ts": ts,
            },
        },
        {
            "type": "system_stat",
            "payload": {
                "label": f"{state['edges_created']} edges mapped",
                "metric": "edges_created",
                "value": state["edges_created"],
                "ts": ts,
            },
        },
        {
            "type": "founder_arc",
            "payload": {
                "label": f"{state['founder_arcs']} founder arcs detected",
                "metric": "founder_arcs",
                "value": state["founder_arcs"],
                "arcs": state["arc_list"],
                "ts": ts,
            },
        },
        {
            "type": "open_loop",
            "payload": {
                "label": f"{state['open_loops']} open loops",
                "metric": "open_loops",
                "value": state["open_loops"],
                "loops": state["loop_list"],
                "ts": ts,
            },
        },
    ]
    return cards


def _insert_cards(cur, cards: list) -> list:
    inserted = []
    for card in cards:
        cur.execute(
            "INSERT INTO feed_items (type, payload) VALUES (%s, %s) RETURNING id",
            (card["type"], json.dumps(card["payload"])),
        )
        row = cur.fetchone()
        inserted.append({"id": str(row[0]), "type": card["type"], "label": card["payload"]["label"]})
    return inserted


def _write_receipt(cur, event: str, payload: dict):
    """Write a chained receipt. Prev hash computed from last row in receipts table."""
    cur.execute(
        "SELECT hash FROM receipts ORDER BY created_at DESC LIMIT 1"
    )
    row = cur.fetchone()
    prev_hash = row[0] if row and row[0] else "0" * 64

    raw = json.dumps({"event": event, "payload": payload}, sort_keys=True) + prev_hash
    h = hashlib.sha256(raw.encode()).hexdigest()

    cur.execute(
        "INSERT INTO receipts (event, payload, hash) VALUES (%s, %s, %s) RETURNING id",
        (event, json.dumps(payload), h),
    )
    return h


def build_feed() -> dict:
    """
    Full feed build cycle:
    1. Query system state
    2. Generate feed cards
    3. Insert cards to feed_items
    4. Write feed_generated receipt
    Returns summary dict.
    """
    with _conn() as conn:
        with conn.cursor() as cur:
            state = _query_system_state(cur)
            cards = _build_cards(state)
            inserted = _insert_cards(cur, cards)
            receipt_hash = _write_receipt(
                cur,
                "feed_generated",
                {
                    "cards_count": len(inserted),
                    "stats": {
                        k: state[k]
                        for k in ("files_scanned", "atoms_created", "edges_created", "founder_arcs", "open_loops")
                    },
                },
            )
        conn.commit()

    return {
        "status": "ok",
        "cards_inserted": len(inserted),
        "cards": inserted,
        "receipt_hash": receipt_hash,
        "state": {
            k: state[k]
            for k in ("files_scanned", "atoms_created", "edges_created", "founder_arcs", "open_loops")
        },
    }
