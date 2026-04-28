"""C19 — Mutation testing gate tests. I8."""
from tools.mutation_gate.gate import MutationGate, MutationOperator, MutationGateReport


def test_empty_gate_fails():
    g = MutationGate(threshold=0.80)
    r = g.evaluate()
    assert r.passed is False
    assert r.total == 0


def test_all_killed_passes():
    g = MutationGate(threshold=0.80)
    for i in range(10):
        g.record("test.py", i, MutationOperator.AOR, killed=True)
    r = g.evaluate()
    assert r.passed is True
    assert r.score == 1.0


def test_threshold_enforcement():
    g = MutationGate(threshold=0.80)
    for i in range(7):
        g.record("f.py", i, MutationOperator.ROR, killed=True)
    for i in range(3):
        g.record("f.py", i+10, MutationOperator.ROR, killed=False)
    r = g.evaluate()
    assert r.killed == 7
    assert r.score == 0.7
    assert r.passed is False


def test_survivors_listed():
    g = MutationGate()
    g.record("a.py", 1, MutationOperator.SDL, killed=False)
    g.record("a.py", 2, MutationOperator.SDL, killed=True)
    assert len(g.survivors()) == 1


def test_mutant_id_deterministic():
    g = MutationGate()
    r1 = g.record("x.py", 5, MutationOperator.LCR, killed=True)
    g2 = MutationGate()
    r2 = g2.record("x.py", 5, MutationOperator.LCR, killed=True)
    assert r1.mutant_id == r2.mutant_id


def test_report_fields():
    g = MutationGate(threshold=0.75)
    g.record("z.py", 1, MutationOperator.SVR, killed=True)
    r = g.evaluate()
    assert isinstance(r, MutationGateReport)
    assert r.threshold == 0.75
