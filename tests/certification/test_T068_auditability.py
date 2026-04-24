# Copyright © 2026 AXIOLEV Holdings LLC. All rights reserved.
"""T-068 — Auditability: audit-log completeness + tamper-evident.

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

_REQUIRED_RECEIPT_FIELDS = {"receipt_id", "name", "payload", "prev_id", "tick", "ts"}

_AUDIT_EVENTS = [
    ("auth.yubikey_verify",      {"user": "founder",  "result": "pass"}),
    ("cps.dispatch",             {"op": "fs.list",    "risk_tier": "R1"}),
    ("dignity.never_event_check",{"result": "no_violation"}),
    ("receipt.emitted",          {"layer": "handrail","verdict": "verified"}),
    ("continuum.event_appended", {"stream": "ns_ops", "seq": 42}),
]


def _make_cert(claims: dict) -> CertificateArtifact:
    sig = "sha256:" + hashlib.sha256(
        json.dumps(claims, sort_keys=True).encode()
    ).hexdigest()[:32]
    return CertificateArtifact(
        subject="auditability.log_integrity",
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


def test_audit_log_completeness_and_tamper_evident(tmp_path):
    """Audit log: all required fields present, hash-chain intact, tamper detectable."""
    path = tmp_path / "audit.jsonl"
    emitter = ReceiptEmitter(path)

    ids = []
    for name, payload in _AUDIT_EVENTS:
        rid = emitter.append(name, payload)
        ids.append(rid)

    assert len(set(ids)) == len(ids), "All receipt IDs must be unique"

    store = ReceiptStore(path)
    records = store.read_all()
    assert len(records) == len(_AUDIT_EVENTS)

    for rec in records:
        missing = _REQUIRED_RECEIPT_FIELDS - set(rec.keys())
        assert not missing, f"Record missing required fields: {missing}"

    assert store.verify_chain() is True

    assert records[0]["prev_id"] == "GENESIS"
    for i in range(1, len(records)):
        assert records[i]["prev_id"] == records[i - 1]["receipt_id"], (
            f"Chain break at tick {records[i]['tick']}"
        )

    # Verify event names are preserved in order
    for i, (name, _) in enumerate(_AUDIT_EVENTS):
        assert records[i]["name"] == name

    cert = _make_cert({
        "log_entries":       len(records),
        "chain_verified":    True,
        "all_fields_present": True,
        "genesis_rooted":    True,
        "unique_ids":        True,
    })
    archive = AlexandrianArchive(root=tmp_path)
    _emit_cert_to_lineage(cert, archive)

    events = archive.read_lineage()
    assert len(events) == 1
    assert events[0]["subject"] == "auditability.log_integrity"
    assert events[0]["claims"]["chain_verified"] is True


def test_audit_log_tamper_detected(tmp_path):
    """Modifying a payload field raises ChainIntegrityError."""
    path = tmp_path / "tamper_audit.jsonl"
    emitter = ReceiptEmitter(path)
    emitter.append("auth.yubikey_verify",      {"user": "founder", "result": "pass"})
    emitter.append("cps.dispatch",             {"op": "fs.list", "risk_tier": "R1"})
    emitter.append("receipt.emitted",          {"verdict": "verified"})

    lines = path.read_text().splitlines()
    rec = json.loads(lines[1])
    rec["payload"]["risk_tier"] = "R4"  # tamper
    lines[1] = json.dumps(rec)
    path.write_text("\n".join(lines) + "\n")

    store = ReceiptStore(path)
    with pytest.raises(ChainIntegrityError):
        store.verify_chain()


def test_empty_audit_log_chain_valid(tmp_path):
    """Empty audit log has trivially valid chain."""
    path = tmp_path / "empty.jsonl"
    path.touch()
    store = ReceiptStore(path)
    assert store.verify_chain() is True
    assert store.read_all() == []
