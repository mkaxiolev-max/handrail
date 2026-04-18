"""Ring 1 — L1 Constitutional Layer integration tests.

Tag: ring1-constitutional-layer-v1
"""
import pytest

from ns.api.schemas.canon import ConstraintClass, ConstitutionalRule, DignityCheck, NeverEvent
from ns.domain.models.integrity import CanonRef, IntegrityState, ProvenanceRecord
from ns.services.canon.promotion_guard import PromotionGuard
from ns.services.canon.service import CanonService

SEVEN_SACRED_IDS = {
    "dignity_kernel",
    "append_only_lineage",
    "receipt_requirement",
    "no_unauthorized_canon",
    "no_deletion_rewriting",
    "no_identity_falsification",
    "truthful_provenance",
}


class TestConstraintClass:
    def test_has_sacred(self):
        assert ConstraintClass.SACRED == "SACRED"

    def test_has_relaxable(self):
        assert ConstraintClass.RELAXABLE == "RELAXABLE"

    def test_only_two_members(self):
        assert set(ConstraintClass) == {ConstraintClass.SACRED, ConstraintClass.RELAXABLE}


class TestConstitutionalRule:
    def test_valid_sacred_rule(self):
        rule = ConstitutionalRule(
            id="dignity_kernel",
            description="Test rule",
            constraint_class=ConstraintClass.SACRED,
        )
        assert rule.constraint_class == ConstraintClass.SACRED
        assert rule.invariant_ref is None

    def test_valid_relaxable_rule(self):
        rule = ConstitutionalRule(
            id="some_policy",
            description="A relaxable policy",
            constraint_class=ConstraintClass.RELAXABLE,
            invariant_ref="I8",
        )
        assert rule.constraint_class == ConstraintClass.RELAXABLE
        assert rule.invariant_ref == "I8"

    def test_extra_fields_forbidden(self):
        with pytest.raises(Exception):
            ConstitutionalRule(
                id="x",
                description="y",
                constraint_class=ConstraintClass.SACRED,
                unknown_field="bad",
            )


class TestDignityCheck:
    def test_passed(self):
        dc = DignityCheck(rule_id="dignity_kernel", passed=True)
        assert dc.passed is True
        assert dc.reason is None

    def test_failed_with_reason(self):
        dc = DignityCheck(rule_id="dignity_kernel", passed=False, reason="violation")
        assert dc.passed is False
        assert dc.reason == "violation"

    def test_extra_fields_forbidden(self):
        with pytest.raises(Exception):
            DignityCheck(rule_id="x", passed=True, extra="nope")


class TestNeverEvent:
    def test_construction(self):
        ne = NeverEvent(
            event_id="ne_001",
            description="Self-destruct attempted",
            rule_id="dignity_kernel",
        )
        assert ne.event_id == "ne_001"
        assert ne.rule_id == "dignity_kernel"

    def test_extra_fields_forbidden(self):
        with pytest.raises(Exception):
            NeverEvent(event_id="x", description="y", rule_id="z", extra="bad")


class TestIntegrityTypes:
    def test_provenance_record(self):
        pr = ProvenanceRecord(source_id="src_001", hash_chain_id="abc123", tick=5)
        assert pr.tick == 5

    def test_canon_ref(self):
        cr = CanonRef(rule_id="dignity_kernel", commit_idx=1)
        assert cr.commit_idx == 1

    def test_integrity_state_defaults(self):
        state = IntegrityState()
        assert state.canon_valid is True
        assert state.lineage_valid is True
        assert state.provenance_valid is True


class TestCanonService:
    def setup_method(self):
        self.svc = CanonService()

    def test_loads_seven_sacred_constraints(self):
        assert self.svc.rule_count() == 7

    def test_all_seven_ids_present(self):
        loaded_ids = {r.id for r in self.svc.get_all_rules()}
        assert loaded_ids == SEVEN_SACRED_IDS

    def test_all_rules_are_sacred(self):
        for rule in self.svc.get_all_rules():
            assert rule.constraint_class == ConstraintClass.SACRED, (
                f"{rule.id} must be SACRED"
            )

    def test_get_rule_by_id(self):
        rule = self.svc.get_rule("dignity_kernel")
        assert rule.id == "dignity_kernel"
        assert rule.constraint_class == ConstraintClass.SACRED

    def test_get_nonexistent_rule_raises(self):
        with pytest.raises(KeyError):
            self.svc.get_rule("nonexistent_rule")

    def test_invariant_refs_populated(self):
        for rule in self.svc.get_all_rules():
            assert rule.invariant_ref is not None, (
                f"{rule.id} must have an invariant_ref"
            )


class TestPromotionGuard:
    def test_stub_raises_not_implemented(self):
        guard = PromotionGuard()
        with pytest.raises(NotImplementedError):
            guard.can_promote("branch_001", {})

    def test_importable(self):
        assert PromotionGuard is not None
