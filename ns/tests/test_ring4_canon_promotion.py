"""Ring 4 — L3 Intake + Canon Promotion Gate tests.

Six-condition gate + I1 + I4 hardware quorum (YubiKey 26116460) + Ring 6 G₂.
Tag: ring-4-canon-promotion-v1
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _passing_context() -> dict:
    from ns.services.loom.service import ConfidenceEnvelope

    return {
        "confidence": ConfidenceEnvelope(
            evidence=0.9, contradiction=0.1, novelty=0.8, stability=0.9
        ),
        "contradiction_weight": 0.10,
        "reconstructability": 0.95,
        "lineage_valid": True,
        "hic_approval": True,
        "pdp_approval": True,
        "quorum_certs": [{"serial": "26116460"}],
        "state": {"coherent": True},
    }


# ---------------------------------------------------------------------------
# verify_hardware_quorum
# ---------------------------------------------------------------------------


class TestVerifyHardwareQuorum:
    def test_single_yubikey_satisfies_quorum(self):
        from ns.services.canon.promotion_guard import verify_hardware_quorum

        assert verify_hardware_quorum([{"serial": "26116460"}]) is True

    def test_missing_yubikey_fails(self):
        from ns.services.canon.promotion_guard import verify_hardware_quorum

        assert verify_hardware_quorum([{"serial": "99999999"}]) is False

    def test_empty_certs_fails(self):
        from ns.services.canon.promotion_guard import verify_hardware_quorum

        assert verify_hardware_quorum([]) is False

    def test_three_certs_with_yubikey_satisfies(self):
        from ns.services.canon.promotion_guard import verify_hardware_quorum

        certs = [{"serial": "26116460"}, {"serial": "11111111"}, {"serial": "22222222"}]
        # f=(3-1)//3=0, threshold=1, len=3>=1 → True
        assert verify_hardware_quorum(certs) is True

    def test_formula_exact_four_certs_with_yubi(self):
        from ns.services.canon.promotion_guard import verify_hardware_quorum

        certs = [{"serial": "26116460"}, {"serial": "A"}, {"serial": "B"}, {"serial": "C"}]
        # f=(4-1)//3=1, threshold=3, len=4>=3 → True
        assert verify_hardware_quorum(certs) is True

    def test_no_yubi_in_three_certs_fails(self):
        from ns.services.canon.promotion_guard import verify_hardware_quorum

        assert verify_hardware_quorum([{"serial": "A"}, {"serial": "B"}, {"serial": "C"}]) is False

    def test_serial_must_be_exact_string(self):
        from ns.services.canon.promotion_guard import verify_hardware_quorum

        # Integer serial does not match
        assert verify_hardware_quorum([{"serial": 26116460}]) is False


# ---------------------------------------------------------------------------
# PromotionGuard — six-condition gate
# ---------------------------------------------------------------------------


class TestPromotionGuard:
    def test_all_conditions_met_returns_true(self):
        from ns.services.canon.promotion_guard import PromotionGuard

        assert PromotionGuard().can_promote("br_001", _passing_context()) is True

    def test_low_confidence_denied(self):
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.loom.service import ConfidenceEnvelope

        ctx = _passing_context()
        # score = 0.45*0.1 + 0.25*0.9 + 0.15*0.1 + 0.15*0.1 = 0.30 < 0.82
        ctx["confidence"] = ConfidenceEnvelope(evidence=0.1, contradiction=0.1, novelty=0.1, stability=0.1)
        assert PromotionGuard().can_promote("br_001", ctx) is False

    def test_confidence_at_threshold_passes(self):
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.loom.service import ConfidenceEnvelope

        ctx = _passing_context()
        # score = 0.45*1.0 + 0.25*1.0 + 0.15*0.5 + 0.15*0.5 = 0.85 >= 0.82
        ctx["confidence"] = ConfidenceEnvelope(evidence=1.0, contradiction=0.0, novelty=0.5, stability=0.5)
        assert PromotionGuard().can_promote("br_001", ctx) is True

    def test_high_contradiction_weight_denied(self):
        from ns.services.canon.promotion_guard import PromotionGuard

        ctx = _passing_context()
        ctx["contradiction_weight"] = 0.30
        assert PromotionGuard().can_promote("br_001", ctx) is False

    def test_contradiction_weight_at_boundary_passes(self):
        from ns.services.canon.promotion_guard import PromotionGuard

        ctx = _passing_context()
        ctx["contradiction_weight"] = 0.25
        assert PromotionGuard().can_promote("br_001", ctx) is True

    def test_low_reconstructability_denied(self):
        from ns.services.canon.promotion_guard import PromotionGuard

        ctx = _passing_context()
        ctx["reconstructability"] = 0.80
        assert PromotionGuard().can_promote("br_001", ctx) is False

    def test_reconstructability_at_threshold_passes(self):
        from ns.services.canon.promotion_guard import PromotionGuard

        ctx = _passing_context()
        ctx["reconstructability"] = 0.90
        assert PromotionGuard().can_promote("br_001", ctx) is True

    def test_lineage_invalid_denied(self):
        from ns.services.canon.promotion_guard import PromotionGuard

        ctx = _passing_context()
        ctx["lineage_valid"] = False
        assert PromotionGuard().can_promote("br_001", ctx) is False

    def test_no_hic_approval_denied(self):
        from ns.services.canon.promotion_guard import PromotionGuard

        ctx = _passing_context()
        ctx["hic_approval"] = False
        assert PromotionGuard().can_promote("br_001", ctx) is False

    def test_no_pdp_approval_denied(self):
        from ns.services.canon.promotion_guard import PromotionGuard

        ctx = _passing_context()
        ctx["pdp_approval"] = False
        assert PromotionGuard().can_promote("br_001", ctx) is False

    def test_missing_quorum_certs_denied(self):
        from ns.services.canon.promotion_guard import PromotionGuard

        ctx = _passing_context()
        ctx["quorum_certs"] = []
        assert PromotionGuard().can_promote("br_001", ctx) is False

    def test_wrong_yubikey_serial_denied(self):
        from ns.services.canon.promotion_guard import PromotionGuard

        ctx = _passing_context()
        ctx["quorum_certs"] = [{"serial": "00000000"}]
        assert PromotionGuard().can_promote("br_001", ctx) is False

    def test_none_confidence_denied(self):
        from ns.services.canon.promotion_guard import PromotionGuard

        ctx = _passing_context()
        ctx["confidence"] = None
        assert PromotionGuard().can_promote("br_001", ctx) is False


# ---------------------------------------------------------------------------
# Receipt emission
# ---------------------------------------------------------------------------


class TestPromotionReceipts:
    def test_success_emits_promoted_receipt(self, tmp_path):
        from ns.services.canon.promotion_guard import PromotionGuard

        result = PromotionGuard().promote(
            "br_001", _passing_context(), receipt_path=tmp_path / "r.jsonl"
        )
        assert result["allowed"] is True
        assert result["receipt_name"] == "canon_promoted_with_hardware_quorum"
        assert result["receipt_id"] is not None
        assert len(result["receipt_id"]) == 64

    def test_failure_emits_denied_receipt(self, tmp_path):
        from ns.services.canon.promotion_guard import PromotionGuard

        ctx = _passing_context()
        ctx["quorum_certs"] = []
        result = PromotionGuard().promote(
            "br_001", ctx, receipt_path=tmp_path / "r.jsonl"
        )
        assert result["allowed"] is False
        assert result["receipt_name"] == "canon_promotion_denied_i9_quorum_missing"

    def test_no_receipt_path_returns_none_receipt_id(self):
        from ns.services.canon.promotion_guard import PromotionGuard

        result = PromotionGuard().promote("br_001", _passing_context())
        assert result["receipt_id"] is None

    def test_receipt_file_written(self, tmp_path):
        import json

        from ns.services.canon.promotion_guard import PromotionGuard

        path = tmp_path / "r.jsonl"
        PromotionGuard().promote("br_001", _passing_context(), receipt_path=path)
        assert path.exists()
        record = json.loads(path.read_text().strip())
        assert record["name"] == "canon_promoted_with_hardware_quorum"

    def test_receipt_names_in_registry(self):
        from ns.domain.receipts.names import RECEIPT_NAMES

        assert "canon_promoted_with_hardware_quorum" in RECEIPT_NAMES
        assert "canon_promotion_denied_i9_quorum_missing" in RECEIPT_NAMES

    def test_ring6_receipt_in_registry(self):
        from ns.domain.receipts.names import RECEIPT_NAMES

        assert "ring6_g2_invariant_checked" in RECEIPT_NAMES


# ---------------------------------------------------------------------------
# I1 — Canon precedes Conversion
# ---------------------------------------------------------------------------


class TestI1CanonPrecedesConversion:
    def test_promotion_guard_separate_from_loom(self):
        from ns.services.canon.promotion_guard import PromotionGuard
        from ns.services.loom.service import LoomService

        assert not isinstance(PromotionGuard(), LoomService)

    def test_loom_has_no_promote_methods(self):
        from ns.services.loom.service import LoomService

        loom = LoomService()
        for attr in ("promote", "promote_to_canon", "write_canon", "commit_canon"):
            assert not hasattr(loom, attr), f"LoomService must not have '{attr}' (I1 violation)"


# ---------------------------------------------------------------------------
# I4 — Hardware quorum on canon changes
# ---------------------------------------------------------------------------


class TestI4HardwareQuorum:
    def test_yubikey_serial_26116460_required(self):
        from ns.services.canon.promotion_guard import verify_hardware_quorum

        assert verify_hardware_quorum([{"serial": "26116460"}]) is True
        assert verify_hardware_quorum([{"serial": "26116461"}]) is False

    def test_no_quorum_in_context_denied(self):
        from ns.services.canon.promotion_guard import PromotionGuard

        ctx = _passing_context()
        ctx["quorum_certs"] = []
        assert PromotionGuard().can_promote("br_001", ctx) is False

    def test_verify_hardware_quorum_exact_function_signature(self):
        from ns.services.canon.promotion_guard import verify_hardware_quorum
        import inspect

        sig = inspect.signature(verify_hardware_quorum)
        assert list(sig.parameters.keys()) == ["quorum_certs"]


# ---------------------------------------------------------------------------
# Ring 6 G₂ invariant integration
# ---------------------------------------------------------------------------


class TestRing6G2Integration:
    def test_ring6_phi_parallel_importable(self):
        from ns.domain.models.g2_invariant import ring6_phi_parallel

        assert callable(ring6_phi_parallel)

    def test_ring6_phi_parallel_non_none_state_true(self):
        from ns.domain.models.g2_invariant import ring6_phi_parallel

        assert ring6_phi_parallel({}) is True
        assert ring6_phi_parallel({"coherent": True}) is True

    def test_ring6_phi_parallel_none_state_false(self):
        from ns.domain.models.g2_invariant import ring6_phi_parallel

        assert ring6_phi_parallel(None) is False

    def test_fano_triples_count_is_seven(self):
        from ns.domain.models.g2_invariant import phi_components

        assert len(phi_components()) == 7

    def test_fano_triples_exact_values(self):
        from ns.domain.models.g2_invariant import FANO_TRIPLES

        expected = ((1, 2, 3), (1, 4, 5), (1, 6, 7), (2, 4, 6), (2, 5, 7), (3, 4, 7), (3, 5, 6))
        assert FANO_TRIPLES == expected

    def test_promotion_fails_when_ring6_state_none(self):
        from ns.services.canon.promotion_guard import PromotionGuard

        ctx = _passing_context()
        ctx["state"] = None
        assert PromotionGuard().can_promote("br_001", ctx) is False

    def test_promotion_succeeds_when_ring6_state_valid(self):
        from ns.services.canon.promotion_guard import PromotionGuard

        ctx = _passing_context()
        ctx["state"] = {"g2": "coherent"}
        assert PromotionGuard().can_promote("br_001", ctx) is True


# ---------------------------------------------------------------------------
# RelationBinding
# ---------------------------------------------------------------------------


class TestRelationBinding:
    def test_bind_returns_binding(self):
        from ns.services.canon.relation_binding import RelationBinder

        binder = RelationBinder()
        binding = binder.bind("canon_001", "supersedes", "canon_000")
        assert binding.subject == "canon_001"
        assert binding.predicate == "supersedes"
        assert binding.object_ == "canon_000"

    def test_binding_tick_starts_at_one(self):
        from ns.services.canon.relation_binding import RelationBinder

        binder = RelationBinder()
        b = binder.bind("a", "relates_to", "b")
        assert b.tick == 1

    def test_multiple_bindings_tick_increments(self):
        from ns.services.canon.relation_binding import RelationBinder

        binder = RelationBinder()
        b1 = binder.bind("a", "p", "b")
        b2 = binder.bind("c", "q", "d")
        assert b2.tick > b1.tick

    def test_all_bindings_returns_list(self):
        from ns.services.canon.relation_binding import RelationBinder

        binder = RelationBinder()
        binder.bind("a", "p", "b")
        binder.bind("c", "q", "d")
        assert len(binder.all_bindings()) == 2

    def test_binding_canon_ref_stored(self):
        from ns.services.canon.relation_binding import RelationBinder

        binder = RelationBinder()
        b = binder.bind("a", "p", "b", canon_ref="rule_001")
        assert b.canon_ref == "rule_001"

    def test_relation_binding_default_fields(self):
        from ns.services.canon.relation_binding import RelationBinding

        rb = RelationBinding(subject="x", predicate="y", object_="z")
        assert rb.canon_ref == ""
        assert rb.tick == 0

    def test_empty_binder_returns_empty_list(self):
        from ns.services.canon.relation_binding import RelationBinder

        assert RelationBinder().all_bindings() == []


# ---------------------------------------------------------------------------
# Canon router — POST /canon/promote
# ---------------------------------------------------------------------------


class TestCanonRouter:
    def test_router_importable(self):
        from ns.api.routers.canon import router

        assert router is not None

    def test_router_has_promote_route(self):
        from ns.api.routers.canon import router

        paths = {r.path for r in router.routes}
        assert "/canon/promote" in paths

    def test_router_prefix_is_canon(self):
        from ns.api.routers.canon import router

        assert router.prefix == "/canon"
