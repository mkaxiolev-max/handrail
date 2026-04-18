"""Oracle v2 tests — ≥5 tests covering C5/C6/C7/C8 (ril-P5).

Tag: ril-oracle-tests-green-v2
"""
from __future__ import annotations

import pytest

from ns.api.schemas.common import IntegrityRouteEffect, RouteIntent
from ns.api.schemas.oracle import (
    ConstitutionalContext,
    HandrailExecutionEnvelope,
    HandrailScope,
    OracleAdjudicationRequest,
    OracleDecision,
    OracleSeverity,
)
from ns.services.oracle import service as oracle_service
from ns.services.oracle import policy_matrix
from ns.services.oracle.adjudicator import adjudicate
from ns.services.oracle import constitutional_overlays, decision_selector, envelope_builder


# ---------------------------------------------------------------------------
# T1 — Schema contract
# ---------------------------------------------------------------------------

class TestOracleSchemas:
    def test_adjudication_request_defaults(self):
        req = OracleAdjudicationRequest(
            request_id="req-001",
            envelope=HandrailExecutionEnvelope(),
        )
        assert req.tick == 0
        assert req.ril_aggregate_score == 1.0
        assert req.ril_route_effect == IntegrityRouteEffect.PASS

    def test_envelope_scope_enum(self):
        env = HandrailExecutionEnvelope(scope=HandrailScope.SOVEREIGN, risk_tier="R4")
        assert env.scope == HandrailScope.SOVEREIGN
        assert env.risk_tier == "R4"

    def test_constitutional_context_defaults(self):
        ctx = ConstitutionalContext()
        assert ctx.g2_phi_parallel is True
        assert ctx.dignity_kernel_invoked is False


# ---------------------------------------------------------------------------
# T2 — Constitutional overlays
# ---------------------------------------------------------------------------

class TestConstitutionalOverlays:
    def test_never_event_blocks(self):
        ctx = ConstitutionalContext(never_events_screened=["auth.bypass"])
        reasons = constitutional_overlays.check_never_events(ctx)
        assert len(reasons) == 1
        assert reasons[0].severity == OracleSeverity.CONSTITUTIONAL

    def test_clean_context_no_blocking(self):
        ctx = ConstitutionalContext(never_events_screened=["fs.read"])
        reasons = constitutional_overlays.check_never_events(ctx)
        assert reasons == []

    def test_g2_phi_parallel_with_valid_state(self):
        ok, reasons = constitutional_overlays.check_g2_phi({"tick": 1})
        assert ok is True
        assert reasons == []

    def test_g2_phi_fails_on_none(self):
        ok, reasons = constitutional_overlays.check_g2_phi(None)
        assert ok is False
        assert len(reasons) == 1
        assert reasons[0].reason_id == "g2_phi_not_parallel"


# ---------------------------------------------------------------------------
# T3 — Envelope builder
# ---------------------------------------------------------------------------

class TestEnvelopeBuilder:
    def test_r3_without_yubikey_blocks(self):
        env = HandrailExecutionEnvelope(risk_tier="R3", yubikey_verified=False)
        conditions = envelope_builder.build_conditions(env)
        yubi_cond = next(c for c in conditions if c.condition_id == "yubikey_gate")
        assert not yubi_cond.satisfied
        blocking = envelope_builder.blocking_from_conditions(conditions)
        assert len(blocking) == 1

    def test_r3_with_yubikey_passes(self):
        env = HandrailExecutionEnvelope(risk_tier="R3", yubikey_verified=True)
        conditions = envelope_builder.build_conditions(env)
        yubi_cond = next(c for c in conditions if c.condition_id == "yubikey_gate")
        assert yubi_cond.satisfied
        blocking = envelope_builder.blocking_from_conditions(conditions)
        assert blocking == []

    def test_r0_no_yubikey_required(self):
        env = HandrailExecutionEnvelope(risk_tier="R0", yubikey_verified=False)
        conditions = envelope_builder.build_conditions(env)
        yubi_cond = next(c for c in conditions if c.condition_id == "yubikey_gate")
        assert yubi_cond.satisfied


# ---------------------------------------------------------------------------
# T4 — Decision selector
# ---------------------------------------------------------------------------

class TestDecisionSelector:
    def test_constitutional_blocking_always_deny(self):
        from ns.api.schemas.oracle import OracleBlockingReason
        reasons = [OracleBlockingReason(
            reason_id="ne_test", description="test", severity=OracleSeverity.CONSTITUTIONAL
        )]
        decision = decision_selector.select_decision(reasons, IntegrityRouteEffect.PASS)
        assert decision == OracleDecision.DENY

    def test_escalate_on_ril_escalate(self):
        decision = decision_selector.select_decision([], IntegrityRouteEffect.ESCALATE)
        assert decision == OracleDecision.ESCALATE

    def test_allow_on_clean_pass(self):
        decision = decision_selector.select_decision([], IntegrityRouteEffect.PASS)
        assert decision == OracleDecision.ALLOW

    def test_defer_on_warn(self):
        decision = decision_selector.select_decision([], IntegrityRouteEffect.WARN)
        assert decision == OracleDecision.DEFER


# ---------------------------------------------------------------------------
# T5 — Policy matrix
# ---------------------------------------------------------------------------

class TestPolicyMatrix:
    def test_never_event_op_is_constitutional(self):
        sev = policy_matrix.op_severity("auth", "bypass", "R0")
        assert sev == OracleSeverity.CONSTITUTIONAL

    def test_r4_tier_is_constitutional(self):
        sev = policy_matrix.op_severity("fs", "read", "R4")
        assert sev == OracleSeverity.CONSTITUTIONAL

    def test_r0_nominal_for_safe_domain(self):
        sev = policy_matrix.op_severity("fs", "list", "R0")
        assert sev == OracleSeverity.NOMINAL

    def test_is_never_event_true(self):
        assert policy_matrix.is_never_event("sys", "self_destruct") is True

    def test_is_never_event_false(self):
        assert policy_matrix.is_never_event("fs", "read") is False


# ---------------------------------------------------------------------------
# T6 — Full adjudication pipeline
# ---------------------------------------------------------------------------

class TestAdjudicationPipeline:
    def _make_req(self, **kwargs) -> OracleAdjudicationRequest:
        defaults = dict(
            request_id="req-test",
            envelope=HandrailExecutionEnvelope(),
            ril_route_effect=IntegrityRouteEffect.PASS,
            ril_aggregate_score=0.95,
        )
        defaults.update(kwargs)
        return OracleAdjudicationRequest(**defaults)

    def test_clean_request_allows(self):
        req = self._make_req()
        resp = adjudicate(req)
        assert resp.decision == OracleDecision.ALLOW
        assert resp.severity == OracleSeverity.NOMINAL
        assert resp.route_intent == RouteIntent.COMMIT

    def test_never_event_denies(self):
        req = self._make_req(
            constitutional_context=ConstitutionalContext(
                never_events_screened=["sys.self_destruct"]
            )
        )
        resp = adjudicate(req)
        assert resp.decision == OracleDecision.DENY
        assert resp.severity == OracleSeverity.CONSTITUTIONAL

    def test_r4_without_yubikey_denies(self):
        req = self._make_req(
            envelope=HandrailExecutionEnvelope(risk_tier="R4", yubikey_verified=False)
        )
        resp = adjudicate(req)
        assert resp.decision == OracleDecision.DENY

    def test_r4_with_yubikey_allows(self):
        req = self._make_req(
            envelope=HandrailExecutionEnvelope(risk_tier="R4", yubikey_verified=True)
        )
        resp = adjudicate(req)
        assert resp.decision == OracleDecision.ALLOW

    def test_ril_escalate_escalates(self):
        req = self._make_req(ril_route_effect=IntegrityRouteEffect.ESCALATE)
        resp = adjudicate(req)
        assert resp.decision == OracleDecision.ESCALATE
        assert resp.route_intent == RouteIntent.ESCALATE

    def test_receipts_always_emitted(self):
        req = self._make_req()
        resp = adjudicate(req)
        assert "ring6_g2_invariant_checked" in resp.receipts_emitted
        assert any("oracle_decision" in r for r in resp.receipts_emitted)

    def test_trace_non_empty(self):
        req = self._make_req()
        resp = adjudicate(req)
        assert len(resp.trace) >= 3

    def test_founder_translation_present(self):
        req = self._make_req()
        resp = adjudicate(req)
        assert resp.founder_translation is not None
        assert len(resp.founder_translation) > 0

    def test_service_evaluate_matches_adjudicate(self):
        req = self._make_req(request_id="req-svc")
        resp_svc = oracle_service.evaluate(req)
        assert resp_svc.request_id == "req-svc"
        assert resp_svc.decision == OracleDecision.ALLOW
