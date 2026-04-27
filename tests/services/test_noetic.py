"""C20 — Noetic mass + fascia + intent kernel tests. I8."""
from services.noetic.mass import NoeticMassRegistry, NoeticNode
from services.noetic.fascia import NoeticFascia
from services.noetic.intent_kernel import IntentKernel, IntentClass
import pytest


def test_mass_zero_for_no_refs():
    reg = NoeticMassRegistry()
    node = reg.register("concept_a")
    assert node.mass == 0.0


def test_mass_increases_with_references():
    reg = NoeticMassRegistry()
    reg.increment("x", 10)
    assert reg._nodes["x"].mass > 0


def test_connect_adds_to_both():
    reg = NoeticMassRegistry()
    reg.connect("a", "b")
    assert "b" in reg._nodes["a"].connections


def test_top_n():
    reg = NoeticMassRegistry()
    reg.increment("heavy", 50)
    reg.increment("light", 1)
    top = reg.top_n(1)
    assert top[0].concept == "heavy"


def test_fascia_bind():
    f = NoeticFascia()
    b = f.bind("mind", "body", 0.8)
    assert b.strength == 0.8


def test_fascia_invalid_strength():
    f = NoeticFascia()
    with pytest.raises(ValueError):
        f.bind("a", "b", 1.5)


def test_fascia_avg_strength():
    f = NoeticFascia()
    f.bind("a", "b", 0.6)
    f.bind("c", "d", 0.4)
    assert f.avg_strength() == 0.5


def test_intent_kernel_classify_query():
    k = IntentKernel()
    sig = k.classify("what is this")
    assert sig.intent_class == IntentClass.QUERY


def test_intent_kernel_classify_action():
    k = IntentKernel()
    sig = k.classify("run the process")
    assert sig.intent_class == IntentClass.ACTION


def test_intent_kernel_history():
    k = IntentKernel()
    k.classify("what")
    k.classify("do this")
    assert len(k.history()) == 2
