"""Ring 3 — L4 The Loom tests.

Reflector functor L : GradientField → Canon.
ConfidenceEnvelope: score = 0.45*evidence + 0.25*(1-contradiction) + 0.15*novelty + 0.15*stability

Tag: ring-3-loom-v1
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# ConfidenceEnvelope
# ---------------------------------------------------------------------------


class TestConfidenceEnvelopeWeights:
    def test_weights_sum_to_one(self):
        from ns.services.loom.service import ConfidenceEnvelope

        w = ConfidenceEnvelope.weights()
        total = sum(w.values())
        assert abs(total - 1.0) < 1e-12

    def test_weight_evidence_is_0_45(self):
        from ns.services.loom.service import ConfidenceEnvelope

        assert ConfidenceEnvelope.weights()["evidence"] == pytest.approx(0.45)

    def test_weight_contradiction_is_0_25(self):
        from ns.services.loom.service import ConfidenceEnvelope

        assert ConfidenceEnvelope.weights()["contradiction"] == pytest.approx(0.25)

    def test_weight_novelty_is_0_15(self):
        from ns.services.loom.service import ConfidenceEnvelope

        assert ConfidenceEnvelope.weights()["novelty"] == pytest.approx(0.15)

    def test_weight_stability_is_0_15(self):
        from ns.services.loom.service import ConfidenceEnvelope

        assert ConfidenceEnvelope.weights()["stability"] == pytest.approx(0.15)


class TestConfidenceEnvelopeScore:
    def test_score_all_ones_zero_contradiction(self):
        from ns.services.loom.service import ConfidenceEnvelope

        ce = ConfidenceEnvelope(evidence=1.0, contradiction=0.0, novelty=1.0, stability=1.0)
        assert ce.score() == pytest.approx(1.0)

    def test_score_all_zeros_full_contradiction(self):
        from ns.services.loom.service import ConfidenceEnvelope

        ce = ConfidenceEnvelope(evidence=0.0, contradiction=1.0, novelty=0.0, stability=0.0)
        assert ce.score() == pytest.approx(0.0)

    def test_score_formula_exact(self):
        from ns.services.loom.service import ConfidenceEnvelope

        e, c, n, s = 0.8, 0.2, 0.5, 0.6
        ce = ConfidenceEnvelope(evidence=e, contradiction=c, novelty=n, stability=s)
        expected = 0.45 * e + 0.25 * (1.0 - c) + 0.15 * n + 0.15 * s
        assert ce.score() == pytest.approx(expected)

    def test_score_half_inputs(self):
        from ns.services.loom.service import ConfidenceEnvelope

        ce = ConfidenceEnvelope(evidence=0.5, contradiction=0.5, novelty=0.5, stability=0.5)
        expected = 0.45 * 0.5 + 0.25 * 0.5 + 0.15 * 0.5 + 0.15 * 0.5
        assert ce.score() == pytest.approx(expected)

    def test_score_zero_novelty_and_stability(self):
        from ns.services.loom.service import ConfidenceEnvelope

        ce = ConfidenceEnvelope(evidence=1.0, contradiction=0.0, novelty=0.0, stability=0.0)
        assert ce.score() == pytest.approx(0.45 + 0.25)


# ---------------------------------------------------------------------------
# LoomMode & ModeSwitcher
# ---------------------------------------------------------------------------


class TestLoomMode:
    def test_seven_stages_exist(self):
        from ns.services.loom.mode_switching import LoomMode

        names = {m.name for m in LoomMode}
        assert names == {"GENERATE", "TEST", "CONTRADICT", "REWEIGHT", "NARRATE", "STORE", "REENTER"}

    def test_values_are_strings(self):
        from ns.services.loom.mode_switching import LoomMode

        for m in LoomMode:
            assert isinstance(m.value, str)

    def test_stage_order_length(self):
        from ns.services.loom.mode_switching import ModeSwitcher

        assert len(ModeSwitcher.stage_order()) == 7

    def test_stage_order_starts_with_generate(self):
        from ns.services.loom.mode_switching import LoomMode, ModeSwitcher

        assert ModeSwitcher.stage_order()[0] == LoomMode.GENERATE

    def test_stage_order_ends_with_reenter(self):
        from ns.services.loom.mode_switching import LoomMode, ModeSwitcher

        assert ModeSwitcher.stage_order()[-1] == LoomMode.REENTER


class TestModeSwitcher:
    def test_initial_stage_is_generate(self):
        from ns.services.loom.mode_switching import LoomMode, ModeSwitcher

        assert ModeSwitcher().current == LoomMode.GENERATE

    def test_advance_through_all_stages(self):
        from ns.services.loom.mode_switching import LoomMode, ModeSwitcher

        switcher = ModeSwitcher()
        order = [LoomMode.GENERATE, LoomMode.TEST, LoomMode.CONTRADICT,
                 LoomMode.REWEIGHT, LoomMode.NARRATE, LoomMode.STORE, LoomMode.REENTER]
        assert switcher.current == order[0]
        for expected in order[1:]:
            switcher.advance()
            assert switcher.current == expected

    def test_advance_at_reenter_stays(self):
        from ns.services.loom.mode_switching import LoomMode, ModeSwitcher

        switcher = ModeSwitcher()
        for _ in range(6):
            switcher.advance()
        assert switcher.current == LoomMode.REENTER
        switcher.advance()
        assert switcher.current == LoomMode.REENTER

    def test_reset_returns_to_generate(self):
        from ns.services.loom.mode_switching import LoomMode, ModeSwitcher

        switcher = ModeSwitcher()
        switcher.advance()
        switcher.advance()
        switcher.reset()
        assert switcher.current == LoomMode.GENERATE


# ---------------------------------------------------------------------------
# LoomReflection
# ---------------------------------------------------------------------------


class TestLoomReflection:
    def test_fields_present(self):
        from ns.integrations.ether import GradientTriple
        from ns.services.loom.mode_switching import LoomMode
        from ns.services.loom.service import ConfidenceEnvelope, LoomReflection

        triple = GradientTriple(subject="ns", predicate="knows", object_="canon")
        env = ConfidenceEnvelope(evidence=0.9, contradiction=0.1, novelty=0.5, stability=0.8)
        ref = LoomReflection(triple=triple, envelope=env, stage=LoomMode.REENTER, narrative="test")
        assert ref.triple is triple
        assert ref.envelope is env
        assert ref.stage == LoomMode.REENTER
        assert ref.narrative == "test"
        assert ref.stored is False

    def test_stored_defaults_false(self):
        from ns.integrations.ether import GradientTriple
        from ns.services.loom.mode_switching import LoomMode
        from ns.services.loom.service import ConfidenceEnvelope, LoomReflection

        ref = LoomReflection(
            triple=GradientTriple(subject="a", predicate="b", object_="c"),
            envelope=ConfidenceEnvelope(evidence=1.0, contradiction=0.0, novelty=1.0, stability=1.0),
            stage=LoomMode.GENERATE,
            narrative="",
        )
        assert ref.stored is False

    def test_contradictions_defaults_empty(self):
        from ns.integrations.ether import GradientTriple
        from ns.services.loom.mode_switching import LoomMode
        from ns.services.loom.service import ConfidenceEnvelope, LoomReflection

        ref = LoomReflection(
            triple=GradientTriple(subject="a", predicate="b", object_="c"),
            envelope=ConfidenceEnvelope(evidence=1.0, contradiction=0.0, novelty=1.0, stability=1.0),
            stage=LoomMode.GENERATE,
            narrative="",
        )
        assert ref.contradictions == []


# ---------------------------------------------------------------------------
# LoomService — reflector functor
# ---------------------------------------------------------------------------


class TestLoomServiceReflect:
    def test_empty_field_returns_empty(self):
        from ns.integrations.ether import GradientField
        from ns.services.loom.service import LoomService

        assert LoomService().reflect(GradientField()) == []

    def test_single_triple_returns_one_reflection(self):
        from ns.integrations.ether import GradientField, GradientTriple
        from ns.services.loom.service import LoomService

        gf = GradientField()
        gf.ingest(GradientTriple(subject="ns", predicate="knows", object_="canon"))
        reflections = LoomService().reflect(gf)
        assert len(reflections) == 1

    def test_multiple_triples_same_count(self):
        from ns.integrations.ether import GradientField, GradientTriple
        from ns.services.loom.service import LoomService

        gf = GradientField()
        for i in range(4):
            gf.ingest(GradientTriple(subject=f"s{i}", predicate="p", object_=i))
        assert len(LoomService().reflect(gf)) == 4

    def test_reflection_stage_is_reenter(self):
        from ns.integrations.ether import GradientField, GradientTriple
        from ns.services.loom.mode_switching import LoomMode
        from ns.services.loom.service import LoomService

        gf = GradientField()
        gf.ingest(GradientTriple(subject="x", predicate="y", object_="z"))
        ref = LoomService().reflect(gf)[0]
        assert ref.stage == LoomMode.REENTER

    def test_reflection_stored_is_true(self):
        from ns.integrations.ether import GradientField, GradientTriple
        from ns.services.loom.service import LoomService

        gf = GradientField()
        gf.ingest(GradientTriple(subject="x", predicate="y", object_="z"))
        assert LoomService().reflect(gf)[0].stored is True

    def test_reflection_has_confidence_envelope(self):
        from ns.integrations.ether import GradientField, GradientTriple
        from ns.services.loom.service import ConfidenceEnvelope, LoomService

        gf = GradientField()
        gf.ingest(GradientTriple(subject="x", predicate="y", object_="z"))
        ref = LoomService().reflect(gf)[0]
        assert isinstance(ref.envelope, ConfidenceEnvelope)

    def test_reflection_score_in_range(self):
        from ns.integrations.ether import GradientField, GradientTriple
        from ns.services.loom.service import LoomService

        gf = GradientField()
        gf.ingest(GradientTriple(subject="ns", predicate="says", object_="canon", confidence=0.9))
        ref = LoomService().reflect(gf)[0]
        assert 0.0 <= ref.envelope.score() <= 1.0

    def test_min_confidence_filters_triples(self):
        from ns.integrations.ether import GradientField, GradientTriple
        from ns.services.loom.service import LoomService

        gf = GradientField()
        gf.ingest(GradientTriple(subject="a", predicate="p", object_="x", confidence=0.9))
        gf.ingest(GradientTriple(subject="b", predicate="p", object_="y", confidence=0.2))
        reflections = LoomService().reflect(gf, min_confidence=0.5)
        assert len(reflections) == 1
        assert reflections[0].triple.subject == "a"

    def test_narrative_contains_score(self):
        from ns.integrations.ether import GradientField, GradientTriple
        from ns.services.loom.service import LoomService

        gf = GradientField()
        gf.ingest(GradientTriple(subject="ns", predicate="knows", object_="canon"))
        ref = LoomService().reflect(gf)[0]
        assert "score=" in ref.narrative

    def test_triple_preserved_in_reflection(self):
        from ns.integrations.ether import GradientField, GradientTriple
        from ns.services.loom.service import LoomService

        gf = GradientField()
        t = GradientTriple(subject="ns", predicate="knows", object_="canon", confidence=0.75)
        gf.ingest(t)
        ref = LoomService().reflect(gf)[0]
        assert ref.triple.subject == "ns"
        assert ref.triple.predicate == "knows"
        assert ref.triple.confidence == pytest.approx(0.75)


# ---------------------------------------------------------------------------
# Contradiction injection (CONTRADICT stage)
# ---------------------------------------------------------------------------


class TestContradictionInjection:
    def test_no_contradictions_by_default(self):
        from ns.integrations.ether import GradientField, GradientTriple
        from ns.services.loom.service import LoomService

        gf = GradientField()
        gf.ingest(GradientTriple(subject="ns", predicate="p", object_="q"))
        ref = LoomService().reflect(gf)[0]
        assert ref.contradictions == []

    def test_injected_contradiction_raises_weight(self):
        from ns.integrations.ether import GradientField, GradientTriple
        from ns.services.loom.service import LoomService

        gf = GradientField()
        gf.ingest(GradientTriple(subject="ns", predicate="p", object_="q", confidence=1.0))
        key = "ns:p:q"
        ref = LoomService().reflect(gf, external_contradictions={key: ["counter_evidence"]})[0]
        assert ref.contradictions == ["counter_evidence"]
        # contradiction raises the contradiction component → lowers score
        ref_clean = LoomService().reflect(GradientField(), external_contradictions={})[:]
        # score with contradiction < score without
        gf2 = GradientField()
        gf2.ingest(GradientTriple(subject="ns", predicate="p", object_="q", confidence=1.0))
        ref_no_c = LoomService().reflect(gf2)[0]
        assert ref.envelope.score() < ref_no_c.envelope.score()

    def test_multiple_contradictions_cap_at_1(self):
        from ns.integrations.ether import GradientField, GradientTriple
        from ns.services.loom.service import LoomService

        gf = GradientField()
        gf.ingest(GradientTriple(subject="a", predicate="b", object_="c"))
        key = "a:b:c"
        many = ["c1", "c2", "c3", "c4", "c5"]
        ref = LoomService().reflect(gf, external_contradictions={key: many})[0]
        assert ref.envelope.contradiction <= 1.0


# ---------------------------------------------------------------------------
# I1 — Canon precedes Conversion
# ---------------------------------------------------------------------------


class TestI1CanonPrecedesConversion:
    def test_loom_service_has_no_canon_promotion_method(self):
        """I1: LoomService must NOT expose a canon promotion / write method."""
        from ns.services.loom.service import LoomService

        loom = LoomService()
        for attr in ("promote", "promote_to_canon", "write_canon", "commit_canon"):
            assert not hasattr(loom, attr), f"LoomService must not have '{attr}' (I1 violation)"

    def test_loom_reflect_does_not_modify_gradient_field(self):
        """Reflecting is non-destructive; the GradientField is unchanged."""
        from ns.integrations.ether import GradientField, GradientTriple
        from ns.services.loom.service import LoomService

        gf = GradientField()
        gf.ingest(GradientTriple(subject="ns", predicate="p", object_="q"))
        LoomService().reflect(gf)
        assert len(gf.surface()) == 1


# ---------------------------------------------------------------------------
# Receipt names include loom entries
# ---------------------------------------------------------------------------


class TestLoomReceiptNames:
    def test_loom_receipt_names_present(self):
        from ns.domain.receipts.names import RECEIPT_NAMES

        required = {
            "loom_reflection_completed",
            "loom_mode_transitioned",
            "loom_contradiction_injected",
        }
        assert required <= RECEIPT_NAMES
