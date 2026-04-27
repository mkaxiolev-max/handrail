"""C05 — MISSING-026: Global Efficiency Ledger tests. I8."""
from services.efficiency_ledger.ledger import GlobalEfficiencyLedger, LedgerEntry


def test_ledger_records_entry():
    l = GlobalEfficiencyLedger()
    e = l.record("op1", cost=10.0, outcome_score=8.0)
    assert isinstance(e, LedgerEntry)


def test_ledger_efficiency_ratio():
    l = GlobalEfficiencyLedger()
    l.record("op1", 10.0, 8.0)
    l.record("op2", 5.0, 5.0)
    assert round(l.efficiency_ratio(), 4) == round(13.0 / 15.0, 4)


def test_ledger_empty_efficiency_is_zero():
    l = GlobalEfficiencyLedger()
    assert l.efficiency_ratio() == 0.0


def test_ledger_summary_has_required_keys():
    l = GlobalEfficiencyLedger()
    l.record("a", 1.0, 1.0)
    s = l.summary()
    for key in ["total_ops", "total_cost", "total_outcome", "efficiency_ratio"]:
        assert key in s


def test_ledger_top_n_efficient():
    l = GlobalEfficiencyLedger()
    l.record("slow", 100.0, 1.0)
    l.record("fast", 1.0, 100.0)
    top = l.top_n_efficient(1)
    assert top[0].op_id == "fast"


def test_ledger_entries_by_tag():
    l = GlobalEfficiencyLedger()
    l.record("a", 1.0, 1.0, tags=["inference"])
    l.record("b", 1.0, 1.0, tags=["io"])
    assert len(l.entries_by_tag("inference")) == 1


def test_ledger_entry_efficiency_property():
    e = LedgerEntry("x", 4.0, 8.0, "t")
    assert e.efficiency == 2.0
