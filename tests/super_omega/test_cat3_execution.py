"""Category 3 — Execution (Computer-equivalent). AXIOLEV © 2026."""
from services.omega_logos.layers.execution import Executor, Task

def test_3_1_task_graph_succeeds():
    ex = Executor()
    t = Task(id="t1", op="ping", args={"x":1})
    r = ex.run(t, lambda a: {"ok": True, "echo": a})
    assert r["ok"] is True and t.status == "ok"

def test_3_2_force_failure_abstains_after_retries():
    ex = Executor(max_retries=1)
    t = Task(id="t2", op="fail", args={})
    def fn(_): raise RuntimeError("nope")
    r = ex.run(t, fn)
    assert r["ok"] is False and r["abstained"] is True and t.status == "abstained"
