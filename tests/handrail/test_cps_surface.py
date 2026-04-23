# Copyright © 2026 Axiolev. All rights reserved.
"""
CPS Action Surface Tests
========================
Covers: audit scanner output, tier dispatch, receipt emission, quorum-required
path rejection, decorator lint failure on bare sites.
"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── Path bootstrap ──────────────────────────────────────────────────────────
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO))

from services.handrail.audit import (
    _SurfaceVisitor,
    _decorator_tier,
    emit,
    scan_repo,
)
from services.handrail.decorators import CPSLintRule, CPSGateError, cps
from services.handrail.router import (
    CPSRouter,
    KenosisProof,
    _gate_r0,
    _gate_r1,
    _gate_r2_confirm,
    _gate_r3_human,
    _gate_r4_quorum,
    route,
)


# ===========================================================================
# 1.  Audit scanner — basic output shape
# ===========================================================================


def test_scan_detects_httpx_get():
    source = textwrap.dedent("""\
        import httpx

        def fetch(url):
            return httpx.get(url)
    """)
    visitor = _SurfaceVisitor(source, "test_module.py")
    import ast
    visitor.visit(ast.parse(source))
    assert any(s["detail"] == "httpx.get" for s in visitor.sites), visitor.sites


def test_scan_detects_subprocess_run():
    source = textwrap.dedent("""\
        import subprocess

        def run_cmd(cmd):
            return subprocess.run(cmd, capture_output=True)
    """)
    visitor = _SurfaceVisitor(source, "test_module.py")
    import ast
    visitor.visit(ast.parse(source))
    assert any(s["detail"] == "subprocess.run" for s in visitor.sites)


def test_scan_detects_override_function_name():
    source = textwrap.dedent("""\
        def bypass_auth(token):
            return True
    """)
    visitor = _SurfaceVisitor(source, "test_module.py")
    import ast
    visitor.visit(ast.parse(source))
    assert any(s["kind"] == "manual_override_entry" for s in visitor.sites)


def test_scan_site_is_tiered_when_cps_decorator_present():
    source = textwrap.dedent("""\
        from services.handrail.decorators import cps
        import httpx

        @cps(tier="R1")
        def fetch(url):
            return httpx.get(url)
    """)
    visitor = _SurfaceVisitor(source, "test_module.py")
    import ast
    visitor.visit(ast.parse(source))
    tiered = [s for s in visitor.sites if s["tiered"]]
    assert tiered, "Expected at least one tiered site when @cps present"


def test_scan_site_untiered_without_decorator():
    source = textwrap.dedent("""\
        import httpx

        def fetch(url):
            return httpx.get(url)
    """)
    visitor = _SurfaceVisitor(source, "test_module.py")
    import ast
    visitor.visit(ast.parse(source))
    untiered = [s for s in visitor.sites if not s["tiered"]]
    assert untiered, "Expected untiered site when @cps absent"


def test_emit_writes_json_to_tmp(tmp_path):
    output = tmp_path / "cps_action_surface.json"
    # Scan just a tiny synthetic directory
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "module.py").write_text("import httpx\ndef f():\n    httpx.get('http://x')\n")

    manifest = emit(tmp_path, output)
    assert output.exists()
    data = json.loads(output.read_text())
    assert data["schema_version"] == "1.0"
    assert "sites" in data
    assert "summary" in data
    assert data["summary"]["total"] == data["summary"]["tiered"] + data["summary"]["untiered"]


# ===========================================================================
# 2.  Risk tier gate logic
# ===========================================================================


def test_r0_always_passes():
    result = _gate_r0()
    assert result.ok


def test_r1_passes_with_default_context():
    result = _gate_r1({})
    assert result.ok  # No confirmed=False → passes


def test_r1_denied_when_confirmed_false():
    result = _gate_r1({"confirmed": False})
    assert not result.ok
    assert "R1" in result.reason


def test_r2_denied_without_confirmed():
    result = _gate_r2_confirm({})
    assert not result.ok


def test_r2_passes_with_confirmed_true():
    result = _gate_r2_confirm({"confirmed": True})
    assert result.ok


def test_r3_denied_without_human_approved():
    result = _gate_r3_human({})
    assert not result.ok
    assert "human_approved" in result.reason


def test_r3_passes_with_human_approved():
    result = _gate_r3_human({"human_approved": True})
    assert result.ok


def test_r4_denied_without_yubikey():
    result = _gate_r4_quorum({"human_approved": True, "quorum_slots_verified": 2})
    assert not result.ok
    assert "yubikey_verified" in result.reason


def test_r4_denied_without_quorum_single_founder():
    result = _gate_r4_quorum({"yubikey_verified": True})
    assert not result.ok  # needs human_approved as second factor


def test_r4_passes_single_founder_mode():
    # 1 YubiKey slot + human_approved = sovereign in single-founder mode
    result = _gate_r4_quorum({
        "yubikey_verified": True,
        "human_approved": True,
    })
    assert result.ok


def test_r4_passes_full_quorum():
    result = _gate_r4_quorum({
        "yubikey_verified": True,
        "quorum_slots_verified": 2,
    })
    assert result.ok


# ===========================================================================
# 3.  Kenosis proof integrity
# ===========================================================================


def test_kenosis_proof_verifies():
    proof = KenosisProof(symbol="send_sms", tier="R2", arg_types=["str", "dict"])
    assert proof.verify()


def test_kenosis_proof_tamper_detected():
    proof = KenosisProof(symbol="send_sms", tier="R2", arg_types=["str"])
    proof.tier = "R0"  # tamper
    assert not proof.verify()


# ===========================================================================
# 4.  CPSRouter — end-to-end dispatch
# ===========================================================================


def _noop_fn(*args, **kwargs):
    return {"called": True, "args": args}


def test_router_r0_calls_fn(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "services.handrail.router._ledger_dir",
        lambda date_str: tmp_path,
    )
    router = CPSRouter()
    result = router.route(
        fn=_noop_fn,
        args=(1, 2),
        kwargs={},
        tier="R0",
        site={"symbol": "_noop_fn", "file": "test.py", "line": 1},
        context={},
    )
    assert result["ok"]
    assert result["result"] == {"called": True, "args": (1, 2)}
    assert Path(result["receipt_path"]).exists()


def test_router_r3_blocked_without_human_approval(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "services.handrail.router._ledger_dir",
        lambda date_str: tmp_path,
    )
    router = CPSRouter()
    result = router.route(
        fn=_noop_fn,
        args=(),
        kwargs={},
        tier="R3",
        site={"symbol": "_noop_fn"},
        context={},  # no human_approved
    )
    assert not result["ok"]
    assert "GATE_DENIED" in (result["error"] or "")
    # Receipt must still be written even on denial
    assert Path(result["receipt_path"]).exists()


def test_router_r4_blocked_without_yubikey(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "services.handrail.router._ledger_dir",
        lambda date_str: tmp_path,
    )
    router = CPSRouter()
    result = router.route(
        fn=_noop_fn,
        args=(),
        kwargs={},
        tier="R4",
        site={"symbol": "_noop_fn"},
        context={"human_approved": True},  # no yubikey_verified
    )
    assert not result["ok"]
    assert "GATE_DENIED" in (result["error"] or "")


def test_router_receipt_has_required_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "services.handrail.router._ledger_dir",
        lambda date_str: tmp_path,
    )
    router = CPSRouter()
    result = router.route(
        fn=_noop_fn,
        args=(),
        kwargs={},
        tier="R1",
        site={"symbol": "_noop_fn", "file": "test.py", "line": 5},
        context={"confirmed": True},
    )
    receipt = json.loads(Path(result["receipt_path"]).read_text())
    for field in ("receipt_version", "action_id", "ts_utc", "tier",
                  "gates", "outcome", "receipt_hash"):
        assert field in receipt, f"Missing field: {field}"


def test_router_r2_includes_kenosis(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "services.handrail.router._ledger_dir",
        lambda date_str: tmp_path,
    )
    router = CPSRouter()
    result = router.route(
        fn=_noop_fn,
        args=(42,),
        kwargs={},
        tier="R2",
        site={"symbol": "_noop_fn"},
        context={"confirmed": True},
    )
    assert result["ok"]
    assert result["kenosis"] is not None
    assert result["kenosis"]["tier"] == "R2"
    receipt = json.loads(Path(result["receipt_path"]).read_text())
    assert receipt["kenosis"] is not None


# ===========================================================================
# 5.  Decorator @cps — gate integration
# ===========================================================================


def test_cps_decorator_r0_passthrough(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "services.handrail.router._ledger_dir",
        lambda date_str: tmp_path,
    )

    @cps(tier="R0")
    def read_data():
        return {"data": 42}

    assert read_data() == {"data": 42}


def test_cps_decorator_r3_raises_on_no_approval(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "services.handrail.router._ledger_dir",
        lambda date_str: tmp_path,
    )

    @cps(tier="R3")
    def high_impact_action():
        return "done"

    with pytest.raises(CPSGateError) as exc_info:
        high_impact_action()  # no _cps_context supplied → no human_approved
    assert exc_info.value.tier == "R3"


def test_cps_decorator_r3_passes_with_human_approval(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "services.handrail.router._ledger_dir",
        lambda date_str: tmp_path,
    )

    @cps(tier="R3")
    def high_impact_action():
        return "done"

    result = high_impact_action(_cps_context={"human_approved": True})
    assert result == "done"


def test_cps_decorator_invalid_tier_raises():
    with pytest.raises(ValueError, match="invalid tier"):
        @cps(tier="R9")
        def fn():
            pass


# ===========================================================================
# 6.  CPSLintRule — decorator lint
# ===========================================================================


def test_lint_clean_when_decorated():
    source = textwrap.dedent("""\
        from services.handrail.decorators import cps
        import httpx

        @cps(tier="R1")
        def fetch(url):
            return httpx.get(url)
    """)
    errors = CPSLintRule.check_source(source, "test.py")
    assert errors == [], f"Expected no errors, got: {errors}"


def test_lint_error_on_bare_httpx_call():
    source = textwrap.dedent("""\
        import httpx

        def fetch(url):
            return httpx.get(url)
    """)
    errors = CPSLintRule.check_source(source, "test.py")
    assert errors, "Expected lint error for undecorated httpx.get"
    assert any("httpx.get" in e["detail"] for e in errors)


def test_lint_error_on_override_fn_without_cps():
    source = textwrap.dedent("""\
        def bypass_auth(token):
            return True
    """)
    errors = CPSLintRule.check_source(source, "test.py")
    assert errors
    assert any("override" in e["kind"] or "bypass" in e["detail"] for e in errors)


def test_lint_no_error_on_subprocess_in_cps_fn():
    source = textwrap.dedent("""\
        import subprocess
        from services.handrail.decorators import cps

        @cps(tier="R2")
        def run(cmd):
            return subprocess.run(cmd, capture_output=True)
    """)
    errors = CPSLintRule.check_source(source, "test.py")
    assert errors == []
