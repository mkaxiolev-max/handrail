# Copyright © 2026 AXIOLEV Holdings LLC. All rights reserved.
"""T-062 — Lineage: Lineage Fabric end-to-end chain integrity.

I7 certification pillar — emits CertificateArtifact to Lineage Fabric on success.
"""
import hashlib
import json
from datetime import datetime, timedelta, timezone

import pytest

from services.assurance import CertificateArtifact
from ns.integrations.alexandria import AlexandrianArchive
from ns.domain.receipts.emitter import ReceiptEmitter
from ns.domain.receipts.store import ReceiptStore, ChainIntegrityError

_ISSUER = "axiolev_dignity_kernel"
_EXPIRY = (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")

_LINEAGE_EVENTS = [
    {"name": "lineage_fabric_appended", "layer": "handrail", "op": "cps_dispatch",    "seq": 1},
    {"name": "lineage_fabric_appended", "layer": "ns",       "op": "receipt_emit",    "seq": 2},
    {"name": "lineage_fabric_appended", "layer": "continuum","op": "event_append",    "seq": 3},
    {"name": "lineage_fabric_appended", "layer": "handrail", "op": "auth_yubikey",    "seq": 4},
    {"name": "lineage_fabric_appended", "layer": "ns",       "op": "dignity_verify",  "seq": 5},
]


def _make_cert(claims: dict) -> CertificateArtifact:
    sig = "sha256:" + hashlib.sha256(
        json.dumps(claims, sort_keys=True).encode()
    ).hexdigest()[:32]
    return CertificateArtifact(
        subject="lineage.chain_integrity",
        claims=claims,
        issuer=_ISSUER,
        signature=sig,
        expiry=_EXPIRY,
    )


def _emit_cert_to_lineage(cert: CertificateArtifact, archive: AlexandrianArchive) -> None:
    archive.append_lineage_event({
        "type": "certificate_artifact",
        "subject": cert.subject,
        "claims": cert.claims,
        "issuer": cert.issuer,
        "signature": cert.signature,
        "expiry": cert.expiry,
    })


def test_lineage_fabric_end_to_end_chain_integrity(tmp_path):
    """Lineage Fabric: append 5 events, read back in order, hash-chain intact."""
    archive = AlexandrianArchive(root=tmp_path)

    for event in _LINEAGE_EVENTS:
        archive.append_lineage_event(event)

    events = archive.read_lineage()
    assert len(events) == len(_LINEAGE_EVENTS)
    for i, event in enumerate(events):
        assert event["seq"] == i + 1, f"Event {i} seq mismatch"
        assert event["layer"] == _LINEAGE_EVENTS[i]["layer"]

    # Also verify ReceiptEmitter hash-chain integrity
    emitter_path = tmp_path / "receipts.jsonl"
    emitter = ReceiptEmitter(emitter_path)
    ids = [emitter.append(e["name"], {"seq": e["seq"]}) for e in _LINEAGE_EVENTS]
    assert len(set(ids)) == len(ids), "All receipt IDs must be unique"

    store = ReceiptStore(emitter_path)
    assert store.verify_chain() is True

    records = store.read_all()
    assert records[0]["prev_id"] == "GENESIS"
    for j in range(1, len(records)):
        assert records[j]["prev_id"] == records[j - 1]["receipt_id"]

    cert = _make_cert({
        "lineage_events": len(events),
        "receipt_chain_depth": len(records),
        "chain_verified": True,
        "genesis_rooted": True,
    })
    _emit_cert_to_lineage(cert, archive)

    final_events = archive.read_lineage()
    cert_event = final_events[-1]
    assert cert_event["subject"] == "lineage.chain_integrity"
    assert cert_event["claims"]["chain_verified"] is True


def test_receipt_chain_tamper_detected(tmp_path):
    """Modifying a receipt record causes ChainIntegrityError."""
    path = tmp_path / "tamper.jsonl"
    emitter = ReceiptEmitter(path)
    emitter.append("lineage_fabric_appended", {"seq": 1})
    emitter.append("lineage_fabric_appended", {"seq": 2})

    lines = path.read_text().splitlines()
    rec = json.loads(lines[0])
    rec["payload"]["seq"] = 999  # tamper
    lines[0] = json.dumps(rec)
    path.write_text("\n".join(lines) + "\n")

    store = ReceiptStore(path)
    with pytest.raises(ChainIntegrityError):
        store.verify_chain()


def test_lineage_fabric_append_only_order(tmp_path):
    """Events read back in strict append order (no reordering)."""
    archive = AlexandrianArchive(root=tmp_path)
    for i in range(5):
        archive.append_lineage_event({"tick": i})
    events = archive.read_lineage()
    ticks = [e["tick"] for e in events]
    assert ticks == list(range(5))
