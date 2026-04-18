"""Ring 2 — L5/L6/L7/L8 Substrate integration tests.

Tag: ring2-substrate-layers-v1
"""
from __future__ import annotations

import json

import pytest


# ---------------------------------------------------------------------------
# Receipt Names
# ---------------------------------------------------------------------------


class TestReceiptNames:
    def test_is_frozenset(self):
        from ns.domain.receipts.names import RECEIPT_NAMES

        assert isinstance(RECEIPT_NAMES, frozenset)

    def test_minimum_cardinality(self):
        from ns.domain.receipts.names import RECEIPT_NAMES

        assert len(RECEIPT_NAMES) >= 22

    def test_t1_names_present(self):
        from ns.domain.receipts.names import RECEIPT_NAMES

        required = {
            "lineage_fabric_appended",
            "alexandrian_lexicon_baptism_receipted",
            "alexandrian_lexicon_drift_blocked",
            "narrative_emitted_with_receipt_hash",
            "ring6_g2_invariant_checked",
            "canon_promoted_with_hardware_quorum",
            "canon_promotion_denied_i9_quorum_missing",
        }
        assert required <= RECEIPT_NAMES

    def test_ril_names_present(self):
        from ns.domain.receipts.names import RECEIPT_NAMES

        assert "ril_evaluation_started" in RECEIPT_NAMES
        assert "ril_drift_checked" in RECEIPT_NAMES
        assert "oracle_received_ril_packet" in RECEIPT_NAMES

    def test_t4_names_reserved(self):
        from ns.domain.receipts.names import RECEIPT_NAMES

        assert "dimensional_contradiction_detected" in RECEIPT_NAMES
        assert "manifold_projection_lawful" in RECEIPT_NAMES


# ---------------------------------------------------------------------------
# Receipt Emitter (I2 append-only, I5 hash-chain)
# ---------------------------------------------------------------------------


class TestReceiptEmitter:
    def test_append_returns_sha256_id(self, tmp_path):
        from ns.domain.receipts.emitter import ReceiptEmitter

        emitter = ReceiptEmitter(tmp_path / "test.jsonl")
        rid = emitter.append("lineage_fabric_appended", {"key": "val"})
        assert isinstance(rid, str)
        assert len(rid) == 64

    def test_deterministic_first_entry(self, tmp_path):
        """Same name/payload at tick 1 from GENESIS → same receipt_id."""
        from ns.domain.receipts.emitter import ReceiptEmitter

        e1 = ReceiptEmitter(tmp_path / "a.jsonl")
        e2 = ReceiptEmitter(tmp_path / "b.jsonl")
        r1 = e1.append("lineage_fabric_appended", {"key": "val"})
        r2 = e2.append("lineage_fabric_appended", {"key": "val"})
        assert r1 == r2

    def test_file_created(self, tmp_path):
        from ns.domain.receipts.emitter import ReceiptEmitter

        path = tmp_path / "receipts.jsonl"
        ReceiptEmitter(path).append("lineage_fabric_appended")
        assert path.exists()

    def test_i2_append_only_grows(self, tmp_path):
        """I2: subsequent appends grow the file, never truncate."""
        from ns.domain.receipts.emitter import ReceiptEmitter

        path = tmp_path / "receipts.jsonl"
        emitter = ReceiptEmitter(path)
        emitter.append("lineage_fabric_appended", {"n": 1})
        size1 = path.stat().st_size
        emitter.append("lineage_fabric_appended", {"n": 2})
        assert path.stat().st_size > size1

    def test_each_line_valid_json_with_required_keys(self, tmp_path):
        from ns.domain.receipts.emitter import ReceiptEmitter

        path = tmp_path / "receipts.jsonl"
        emitter = ReceiptEmitter(path)
        emitter.append("lineage_fabric_appended", {"x": 1})
        emitter.append("alexandrian_lexicon_baptism_receipted", {"y": 2})
        for line in path.read_text().splitlines():
            record = json.loads(line)
            assert "receipt_id" in record
            assert "name" in record
            assert "tick" in record
            assert "prev_id" in record
            assert "ts" in record

    def test_tick_increments(self, tmp_path):
        from ns.domain.receipts.emitter import ReceiptEmitter

        path = tmp_path / "receipts.jsonl"
        emitter = ReceiptEmitter(path)
        for name in ("a", "b", "c"):
            emitter.append(name)
        records = [json.loads(l) for l in path.read_text().splitlines()]
        assert [r["tick"] for r in records] == [1, 2, 3]

    def test_prev_id_chain(self, tmp_path):
        from ns.domain.receipts.emitter import ReceiptEmitter

        path = tmp_path / "receipts.jsonl"
        emitter = ReceiptEmitter(path)
        emitter.append("lineage_fabric_appended")
        emitter.append("alexandrian_lexicon_baptism_receipted")
        records = [json.loads(l) for l in path.read_text().splitlines()]
        assert records[0]["prev_id"] == "GENESIS"
        assert records[1]["prev_id"] == records[0]["receipt_id"]

    def test_no_payload_defaults_to_empty_dict(self, tmp_path):
        from ns.domain.receipts.emitter import ReceiptEmitter

        path = tmp_path / "receipts.jsonl"
        ReceiptEmitter(path).append("lineage_fabric_appended")
        record = json.loads(path.read_text().strip())
        assert record["payload"] == {}


# ---------------------------------------------------------------------------
# Receipt Store (I5 hash-chain verification)
# ---------------------------------------------------------------------------


class TestReceiptStore:
    def test_verify_valid_chain(self, tmp_path):
        from ns.domain.receipts.emitter import ReceiptEmitter
        from ns.domain.receipts.store import ReceiptStore

        path = tmp_path / "chain.jsonl"
        emitter = ReceiptEmitter(path)
        emitter.append("lineage_fabric_appended", {"n": 1})
        emitter.append("canon_promoted_with_hardware_quorum", {"n": 2})
        assert ReceiptStore(path).verify_chain() is True

    def test_read_all_returns_records_in_order(self, tmp_path):
        from ns.domain.receipts.emitter import ReceiptEmitter
        from ns.domain.receipts.store import ReceiptStore

        path = tmp_path / "chain.jsonl"
        emitter = ReceiptEmitter(path)
        emitter.append("lineage_fabric_appended")
        emitter.append("narrative_emitted_with_receipt_hash")
        records = ReceiptStore(path).read_all()
        assert len(records) == 2
        assert records[0]["name"] == "lineage_fabric_appended"
        assert records[1]["name"] == "narrative_emitted_with_receipt_hash"

    def test_empty_path_returns_empty_list(self, tmp_path):
        from ns.domain.receipts.store import ReceiptStore

        assert ReceiptStore(tmp_path / "missing.jsonl").read_all() == []

    def test_tampered_hash_raises_chain_integrity_error(self, tmp_path):
        from ns.domain.receipts.emitter import ReceiptEmitter
        from ns.domain.receipts.store import ChainIntegrityError, ReceiptStore

        path = tmp_path / "chain.jsonl"
        ReceiptEmitter(path).append("lineage_fabric_appended")
        record = json.loads(path.read_text().strip())
        record["receipt_id"] = "deadbeef" * 8
        path.write_text(json.dumps(record) + "\n")
        with pytest.raises(ChainIntegrityError):
            ReceiptStore(path).verify_chain()

    def test_tampered_prev_id_raises_chain_integrity_error(self, tmp_path):
        from ns.domain.receipts.emitter import ReceiptEmitter
        from ns.domain.receipts.store import ChainIntegrityError, ReceiptStore

        path = tmp_path / "chain.jsonl"
        emitter = ReceiptEmitter(path)
        emitter.append("lineage_fabric_appended")
        emitter.append("narrative_emitted_with_receipt_hash")
        lines = path.read_text().splitlines()
        rec = json.loads(lines[1])
        rec["prev_id"] = "0" * 64
        path.write_text(lines[0] + "\n" + json.dumps(rec) + "\n")
        with pytest.raises(ChainIntegrityError):
            ReceiptStore(path).verify_chain()


# ---------------------------------------------------------------------------
# Alexandrian Archive (L5/L6/L7/L8)
# ---------------------------------------------------------------------------


class TestAlexandrianArchive:
    def test_alias_is_class(self):
        from ns.integrations.alexandria import AlexandrianArchive, alexandrian_archive

        assert alexandrian_archive is AlexandrianArchive

    def test_instantiate_with_override(self, tmp_path):
        from ns.integrations.alexandria import AlexandrianArchive

        archive = AlexandrianArchive(root=tmp_path)
        assert archive.root == tmp_path

    def test_layout_dirs_created(self, tmp_path):
        from ns.integrations.alexandria import AlexandrianArchive

        AlexandrianArchive(root=tmp_path)
        assert (tmp_path / "branches").is_dir()
        assert (tmp_path / "ledger").is_dir()
        assert (tmp_path / "lexicon").is_dir()
        assert (tmp_path / "state" / "transitions").is_dir()
        assert (tmp_path / "narrative").is_dir()
        assert (tmp_path / "canon").is_dir()
        assert (tmp_path / "projections").is_dir()

    def test_branch_roundtrip(self, tmp_path):
        from ns.integrations.alexandria import AlexandrianArchive

        archive = AlexandrianArchive(root=tmp_path)
        archive.write_branch("br_001", {"commit_idx": 1, "spec": "dignity"})
        assert archive.read_branch("br_001")["commit_idx"] == 1

    def test_projection_roundtrip(self, tmp_path):
        from ns.integrations.alexandria import AlexandrianArchive

        archive = AlexandrianArchive(root=tmp_path)
        archive.write_projection("proj_001", {"type": "state_snapshot"})
        assert archive.read_projection("proj_001")["type"] == "state_snapshot"

    def test_lineage_i2_append_only(self, tmp_path):
        """I2: Lineage Fabric events are strictly append-only."""
        from ns.integrations.alexandria import AlexandrianArchive

        archive = AlexandrianArchive(root=tmp_path)
        archive.append_lineage_event({"name": "lineage_fabric_appended", "tick": 1})
        archive.append_lineage_event({"name": "lineage_fabric_appended", "tick": 2})
        events = archive.read_lineage()
        assert len(events) == 2
        assert events[0]["tick"] == 1
        assert events[1]["tick"] == 2

    def test_lexicon_baptism_locked_ontology(self, tmp_path):
        """L5 Alexandrian Lexicon: baptism records are append-only (I10)."""
        from ns.integrations.alexandria import AlexandrianArchive

        archive = AlexandrianArchive(root=tmp_path)
        archive.baptize("Gradient Field", "L2 layer (formerly Ether)", "PROMPT.md")
        archive.baptize("Alexandrian Lexicon", "L5 layer (formerly Atomlex)", "PROMPT.md")
        baptisms = archive.read_baptisms()
        assert len(baptisms) == 2
        assert baptisms[0]["term"] == "Gradient Field"

    def test_lexicon_supersession_not_deletion(self, tmp_path):
        """I10: supersede only — original baptism must remain after supersession."""
        from ns.integrations.alexandria import AlexandrianArchive

        archive = AlexandrianArchive(root=tmp_path)
        archive.baptize("Ether", "deprecated name", "legacy")
        archive.supersede("Ether", "Gradient Field", "locked ontology rename")
        supersessions = archive.read_supersessions()
        assert len(supersessions) == 1
        assert supersessions[0]["old_term"] == "Ether"
        assert supersessions[0]["new_term"] == "Gradient Field"
        assert len(archive.read_baptisms()) == 1

    def test_state_shard_append_only(self, tmp_path):
        """L6 State Manifold: shard deltas are append-only."""
        from ns.integrations.alexandria import AlexandrianArchive

        archive = AlexandrianArchive(root=tmp_path)
        archive.append_state_delta("shard_001", {"key": "a", "val": 1})
        archive.append_state_delta("shard_001", {"key": "a", "val": 2})
        deltas = archive.read_state_deltas("shard_001")
        assert len(deltas) == 2
        assert deltas[0]["val"] == 1
        assert deltas[1]["val"] == 2

    def test_shard_manifest_written(self, tmp_path):
        from ns.integrations.alexandria import AlexandrianArchive

        archive = AlexandrianArchive(root=tmp_path)
        archive.write_shard_manifest("shard_001", {"shard_id": "shard_001", "version": 1})
        manifest_path = tmp_path / "state" / "shards" / "shard_001" / "manifest.json"
        assert manifest_path.exists()
        assert json.loads(manifest_path.read_text())["version"] == 1

    def test_multiple_shards_independent(self, tmp_path):
        from ns.integrations.alexandria import AlexandrianArchive

        archive = AlexandrianArchive(root=tmp_path)
        archive.append_state_delta("shard_A", {"x": 1})
        archive.append_state_delta("shard_B", {"y": 2})
        assert len(archive.read_state_deltas("shard_A")) == 1
        assert len(archive.read_state_deltas("shard_B")) == 1


# ---------------------------------------------------------------------------
# Gradient Field (L2)
# ---------------------------------------------------------------------------


class TestGradientField:
    def test_alias_is_class(self):
        from ns.integrations.ether import GradientField, gradient_field

        assert gradient_field is GradientField

    def test_ingest_and_surface(self):
        from ns.integrations.ether import GradientField, GradientTriple

        gf = GradientField()
        gf.ingest(GradientTriple(subject="user", predicate="says", object_="hello"))
        results = gf.surface()
        assert len(results) == 1
        assert results[0].subject == "user"

    def test_surface_filters_by_confidence(self):
        from ns.integrations.ether import GradientField, GradientTriple

        gf = GradientField()
        gf.ingest(GradientTriple(subject="a", predicate="p", object_="x", confidence=0.9))
        gf.ingest(GradientTriple(subject="b", predicate="p", object_="y", confidence=0.3))
        assert len(gf.surface(min_confidence=0.8)) == 1
        assert gf.surface(min_confidence=0.8)[0].subject == "a"

    def test_clear_empties_field(self):
        from ns.integrations.ether import GradientField, GradientTriple

        gf = GradientField()
        gf.ingest(GradientTriple(subject="a", predicate="p", object_="x"))
        gf.clear()
        assert gf.surface() == []

    def test_gradient_triple_defaults(self):
        from ns.integrations.ether import GradientTriple

        t = GradientTriple(subject="s", predicate="p", object_=42)
        assert t.confidence == 1.0
        assert t.tick == 0

    def test_multiple_triples_surface_all(self):
        from ns.integrations.ether import GradientField, GradientTriple

        gf = GradientField()
        for i in range(5):
            gf.ingest(GradientTriple(subject=f"s{i}", predicate="p", object_=i))
        assert len(gf.surface()) == 5
