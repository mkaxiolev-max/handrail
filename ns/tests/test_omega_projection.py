"""Z3.6 — Omega L10 Projection/Ego Layer tests.

Coverage:
  - 6 recovery strategies exercised (one test each)
  - 6 projection modes return valid ProjectionResult
  - ConfidenceEnvelope.score() with fixed inputs
  - order_used is recorded and non-empty
  - Receipt projection_emitted lands in ledger
  - Canon gate still refuses unauthorized promotion after Omega is live
  - Abstention returns mode=PARTIAL_RECONSTRUCTION when all strategies fail
  - Primitives validation (Pydantic v2 constraints)
  - OmegaStore read/write/append_receipt
  - Storytime model and router
  - ProjectionResult serialization round-trip

AXIOLEV Holdings LLC © 2026
"""
from __future__ import annotations

import json
import tempfile
import uuid
from pathlib import Path
from typing import Generator

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_store(tmp_path: Path):
    """OmegaStore backed by a temp directory."""
    from ns.integrations.omega_store import OmegaStore
    return OmegaStore(root=tmp_path)


@pytest.fixture()
def engine(tmp_store):
    """ProjectionEngine backed by a temp OmegaStore."""
    from ns.services.omega.projection_engine import ProjectionEngine
    return ProjectionEngine(store=tmp_store)


def _req(target_ref: str, mode_str: str = "exact_view", **kwargs):
    from ns.domain.models.omega_primitives import ProjectionMode, ProjectionRequest
    return ProjectionRequest(
        target_ref=target_ref,
        mode=ProjectionMode(mode_str),
        requested_by="test_agent",
        **kwargs,
    )


# ---------------------------------------------------------------------------
# ConfidenceEnvelope
# ---------------------------------------------------------------------------


class TestConfidenceEnvelope:
    def test_score_known_values(self):
        from ns.domain.models.omega_primitives import ConfidenceEnvelope
        env = ConfidenceEnvelope(evidence=1.0, contradiction=0.0, novelty=1.0, stability=1.0)
        # 0.45*1 + 0.25*(1-0) + 0.15*1 + 0.15*1 = 1.0
        assert abs(env.score() - 1.0) < 1e-9

    def test_score_zero_evidence(self):
        from ns.domain.models.omega_primitives import ConfidenceEnvelope
        env = ConfidenceEnvelope(evidence=0.0, contradiction=1.0, novelty=0.0, stability=0.0)
        # 0 + 0 + 0 + 0 = 0.0
        assert abs(env.score() - 0.0) < 1e-9

    def test_score_partial(self):
        from ns.domain.models.omega_primitives import ConfidenceEnvelope
        env = ConfidenceEnvelope(evidence=0.8, contradiction=0.2, novelty=0.5, stability=0.6)
        expected = 0.45 * 0.8 + 0.25 * (1 - 0.2) + 0.15 * 0.5 + 0.15 * 0.6
        assert abs(env.score() - expected) < 1e-9

    def test_immutable(self):
        from ns.domain.models.omega_primitives import ConfidenceEnvelope
        env = ConfidenceEnvelope(evidence=0.5, contradiction=0.1, novelty=0.2, stability=0.3)
        with pytest.raises(Exception):
            env.evidence = 0.9  # type: ignore[misc]

    def test_bounds_validation(self):
        from ns.domain.models.omega_primitives import ConfidenceEnvelope
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            ConfidenceEnvelope(evidence=1.1, contradiction=0.0, novelty=0.0, stability=0.0)


# ---------------------------------------------------------------------------
# Six recovery strategies
# ---------------------------------------------------------------------------


class TestRecoveryStrategies:
    def test_strategy_exact_local_cache_hit(self, engine, tmp_store):
        """exact_local returns cached projection when one exists."""
        from ns.domain.models.omega_primitives import ProjectionMode
        ref = "branch_exact_001"
        # Pre-seed a cached projection
        tmp_store.write_projection(ref, {"mode": "exact_view", "cached": True})
        result = engine.project(_req(ref, "exact_view"))
        assert result.order_used[0] == "exact_local"
        assert result.recoverability.value == "exact"

    def test_strategy_exact_local_branch_hit(self, engine, tmp_store):
        """exact_local also succeeds via branch data."""
        ref = "branch_exact_002"
        tmp_store.write_branch(ref, {"id": ref, "title": "test", "lineage": []})
        result = engine.project(_req(ref, "branch_view"))
        assert result.order_used[0] == "exact_local"
        assert "exact_local" in result.content["source"]

    def test_strategy_delta_replay(self, engine, tmp_store):
        """delta_replay succeeds when deltas.jsonl exists."""
        ref = "shard_delta_001"
        shard_dir = tmp_store.root / "state" / "shards" / ref
        shard_dir.mkdir(parents=True, exist_ok=True)
        with open(shard_dir / "deltas.jsonl", "w") as f:
            f.write(json.dumps({"op": "add", "seq": 0, "payload": {}}) + "\n")
        result = engine.project(_req(ref, "branch_view"))
        assert "delta_replay" in result.order_used
        assert result.content["source"] == "delta_replay"
        assert result.recoverability.value == "lossless_structural"

    def test_strategy_shard_recovery(self, engine, tmp_store):
        """shard_recovery succeeds when manifest.json exists."""
        ref = "shard_erasure_001"
        shard_dir = tmp_store.root / "shards" / ref
        shard_dir.mkdir(parents=True, exist_ok=True)
        manifest = {"id": ref, "shards": ["s0", "s1"], "erasure_scheme": "rs(10,4)", "merkle_root": "abc"}
        (shard_dir / "manifest.json").write_text(json.dumps(manifest))
        result = engine.project(_req(ref, "merged_view"))
        assert "shard_recovery" in result.order_used
        assert result.content["source"] == "shard_recovery"
        assert result.recoverability.value == "lossless_structural"

    def test_strategy_entanglement_assisted(self, engine, tmp_store):
        """entanglement_assisted succeeds when an entanglement references the target."""
        ref = "node_ent_001"
        ent_dir = tmp_store.root / "entanglements"
        ent_id = str(uuid.uuid4())
        (ent_dir / f"{ent_id}.json").write_text(json.dumps({
            "id": ent_id, "a_ref": ref, "b_ref": "other",
            "kind": "coref", "weight": 0.8,
        }))
        result = engine.project(_req(ref, "canon_view"))
        assert "entanglement_assisted" in result.order_used
        assert result.content["source"] == "entanglement_assisted"
        assert result.recoverability.value == "lossless_semantic"

    def test_strategy_semantic_always_succeeds(self, engine):
        """semantic strategy always returns a result (lossy)."""
        ref = "unknown_node_999"
        result = engine.project(_req(ref, "contrastive_view"))
        assert "semantic" in result.order_used
        assert result.content["source"] == "semantic"
        assert result.content.get("approximated") is True
        assert result.recoverability.value == "lossy_semantic"

    def test_strategy_graceful_partial_abstention(self, engine, tmp_store, monkeypatch):
        """graceful_partial triggers when all earlier strategies disabled."""
        from ns.services.omega import projection_engine as pe
        # Patch semantic to return None to force graceful_partial
        monkeypatch.setattr(engine, "_semantic", lambda req: None)
        ref = "unreachable_ref_999"
        result = engine.project(_req(ref, "exact_view"))
        assert result.order_used[-1] == "graceful_partial"
        assert result.content.get("gap") is True
        assert result.recoverability.value == "irrecoverable"
        from ns.domain.models.omega_primitives import ProjectionMode
        assert result.mode == ProjectionMode.PARTIAL_RECONSTRUCTION


# ---------------------------------------------------------------------------
# Six projection modes
# ---------------------------------------------------------------------------


class TestProjectionModes:
    @pytest.mark.parametrize("mode_str", [
        "exact_view", "branch_view", "merged_view",
        "canon_view", "partial_reconstruction", "contrastive_view",
    ])
    def test_mode_returns_valid_result(self, engine, mode_str):
        from ns.domain.models.omega_primitives import ProjectionResult
        result = engine.project(_req(f"ref_{mode_str}", mode_str))
        assert isinstance(result, ProjectionResult)
        assert result.order_used  # non-empty
        assert result.confidence.score() >= 0.0


# ---------------------------------------------------------------------------
# order_used is recorded and non-empty
# ---------------------------------------------------------------------------


class TestOrderUsed:
    def test_order_used_non_empty(self, engine):
        result = engine.project(_req("some_ref", "exact_view"))
        assert len(result.order_used) >= 1

    def test_order_used_respects_strategy_sequence(self, engine, tmp_store):
        """Strategies are attempted in STRATEGIES order."""
        from ns.services.omega.projection_engine import STRATEGIES
        strategy_names = [s[0] for s in STRATEGIES]
        result = engine.project(_req("new_unknown_ref_abc", "branch_view"))
        for i, name in enumerate(result.order_used):
            assert strategy_names.index(name) == i


# ---------------------------------------------------------------------------
# Receipt projection_emitted lands in ledger
# ---------------------------------------------------------------------------


class TestReceiptLedger:
    def test_projection_emitted_in_ledger(self, engine, tmp_store):
        engine.project(_req("ledger_test_ref", "exact_view"))
        ledger = tmp_store.read_ledger()
        names = [r.get("name") for r in ledger]
        assert "projection_emitted" in names

    def test_ledger_is_hash_chained(self, engine, tmp_store):
        engine.project(_req("chain_ref_1", "exact_view"))
        engine.project(_req("chain_ref_2", "branch_view"))
        ledger = tmp_store.read_ledger()
        assert len(ledger) >= 2
        # Each record has event_hash and prev_hash
        for record in ledger:
            assert "event_hash" in record
            assert "prev_hash" in record

    def test_ledger_receipt_contains_target_ref(self, engine, tmp_store):
        ref = "specific_receipt_ref_xyz"
        engine.project(_req(ref, "exact_view"))
        ledger = tmp_store.read_ledger()
        found = [r for r in ledger if r.get("target_ref") == ref]
        assert len(found) >= 1


# ---------------------------------------------------------------------------
# Canon gate still refuses unauthorized promotion after Omega is live
# ---------------------------------------------------------------------------


class TestCanonGateIntegrity:
    def test_canon_gate_refuses_no_yubikey(self):
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.loom.service import ConfidenceEnvelope
        guard = PromotionGuard()
        ctx = {
            "confidence": ConfidenceEnvelope(
                evidence=0.95, contradiction=0.05, novelty=0.9, stability=0.95
            ),
            "contradiction_weight": 0.05,
            "reconstructability": 0.95,
            "lineage_valid": True,
            "hic_approval": True,
            "pdp_approval": True,
            "quorum_certs": [{"serial": "99999999"}],  # wrong serial
            "state": {"coherent": True},
        }
        assert guard.can_promote("branch_x", ctx) is False

    def test_canon_gate_refuses_low_confidence(self):
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.loom.service import ConfidenceEnvelope
        guard = PromotionGuard()
        ctx = {
            "confidence": ConfidenceEnvelope(
                evidence=0.3, contradiction=0.5, novelty=0.1, stability=0.1
            ),
            "contradiction_weight": 0.05,
            "reconstructability": 0.95,
            "lineage_valid": True,
            "hic_approval": True,
            "pdp_approval": True,
            "quorum_certs": [{"serial": "26116460"}],
            "state": {"coherent": True},
        }
        assert guard.can_promote("branch_y", ctx) is False

    def test_omega_projection_does_not_call_promote(self, engine, monkeypatch):
        """Omega must never invoke PromotionGuard.promote (I1)."""
        called = []
        from ns.services.canon import promotion_guard

        original = promotion_guard.PromotionGuard.promote

        def spy_promote(self, *args, **kwargs):
            called.append(True)
            return original(self, *args, **kwargs)

        monkeypatch.setattr(promotion_guard.PromotionGuard, "promote", spy_promote)
        engine.project(_req("omega_canon_test_ref", "canon_view"))
        assert called == [], "Omega must NOT call PromotionGuard.promote (I1 violation)"


# ---------------------------------------------------------------------------
# OmegaStore primitives
# ---------------------------------------------------------------------------


class TestOmegaStore:
    def test_write_read_json(self, tmp_store):
        tmp_store.write_json("test/foo.json", {"key": "value"})
        data = tmp_store.read_json("test/foo.json")
        assert data == {"key": "value"}

    def test_read_missing_returns_none(self, tmp_store):
        assert tmp_store.read_json("nonexistent/path.json") is None

    def test_append_receipt_increments_tick(self, tmp_store):
        h1 = tmp_store.append_receipt({"name": "evt_1"})
        h2 = tmp_store.append_receipt({"name": "evt_2"})
        assert h1 != h2
        ledger = tmp_store.read_ledger()
        ticks = [r["tick"] for r in ledger]
        assert ticks == sorted(ticks)


# ---------------------------------------------------------------------------
# Storytime primitives
# ---------------------------------------------------------------------------


class TestStorytime:
    def test_storytime_model(self):
        from ns.domain.models.omega_primitives import Storytime
        st = Storytime(
            id="st_001",
            projection_ref="proj_ref_001",
            narrative="The system achieved coherence.",
            arc=["phase_1", "phase_2"],
        )
        assert st.id == "st_001"
        assert len(st.arc) == 2

    def test_storytime_store_roundtrip(self, tmp_store):
        from ns.domain.models.omega_primitives import Storytime
        st = Storytime(
            id="st_002",
            projection_ref="proj_ref_002",
            narrative="Narrative text.",
        )
        tmp_store.write_storytime("st_002", st.model_dump(mode="json"))
        loaded = tmp_store.read_storytime("st_002")
        assert loaded is not None
        assert loaded["narrative"] == "Narrative text."


# ---------------------------------------------------------------------------
# ProjectionResult serialization
# ---------------------------------------------------------------------------


class TestProjectionResultSerialization:
    def test_round_trip(self, engine):
        result = engine.project(_req("serial_test_ref", "branch_view"))
        data = result.model_dump(mode="json")
        from ns.domain.models.omega_primitives import ProjectionResult
        restored = ProjectionResult(**data)
        assert restored.target_ref == result.target_ref
        assert restored.mode == result.mode
        assert restored.recoverability == result.recoverability
