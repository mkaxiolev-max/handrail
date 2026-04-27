"""C23 — Aletheia-Ω 5-step loop tests. I8."""
from services.aletheia_omega.loop import AletheiaOmegaLoop, AletheiaStep
import pytest


def test_start_cycle():
    loop = AletheiaOmegaLoop()
    s = loop.start_cycle()
    assert s.step == AletheiaStep.OBSERVE
    assert s.cycle == 1


def test_full_cycle_accepted():
    loop = AletheiaOmegaLoop()
    loop.start_cycle()
    loop.observe(["low test coverage"])
    loop.analyze(["missing edge cases"])
    loop.hypothesize("add boundary tests")
    loop.test(True)
    s = loop.integrate(True)
    assert s.integrated is True


def test_full_cycle_rejected():
    loop = AletheiaOmegaLoop()
    loop.start_cycle()
    loop.observe([])
    loop.analyze([])
    loop.hypothesize("risky refactor")
    loop.test(False)
    s = loop.integrate(True)
    assert s.integrated is False  # test failed so not integrated


def test_cycle_count():
    loop = AletheiaOmegaLoop()
    for _ in range(3):
        loop.start_cycle()
        loop.observe([])
        loop.analyze([])
        loop.hypothesize("h")
        loop.test(True)
        loop.integrate(True)
    assert loop.cycle_count() == 3


def test_integrated_count():
    loop = AletheiaOmegaLoop()
    loop.start_cycle()
    loop.observe([])
    loop.analyze([])
    loop.hypothesize("h")
    loop.test(True)
    loop.integrate(True)
    assert loop.integrated_count() == 1


def test_receipt_hash_unique():
    loop = AletheiaOmegaLoop()
    s1 = loop.start_cycle()
    loop.observe([])
    loop.analyze([])
    s1 = loop.hypothesize("h1")
    loop.test(True)
    loop.integrate(True)
    loop.start_cycle()
    loop.observe([])
    loop.analyze([])
    s2 = loop.hypothesize("h2")
    loop.test(True)
    loop.integrate(True)
    assert loop.history()[0].receipt_hash != loop.history()[1].receipt_hash


def test_history_all_states():
    loop = AletheiaOmegaLoop()
    loop.start_cycle()
    loop.observe([])
    loop.analyze([])
    loop.hypothesize("x")
    loop.test(True)
    loop.integrate(True)
    assert len(loop.history()) == 1
