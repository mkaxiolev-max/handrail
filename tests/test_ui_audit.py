import pytest
from pathlib import Path
from services.ui_audit import UIAuditor, UIRegenerator, Severity

def test_audit_missing_root():
    findings=UIAuditor("/nonexistent/path").audit()
    assert any(f.severity==Severity.BLOCKER for f in findings)

def test_regenerate_creates_components(tmp_path):
    created=UIRegenerator(str(tmp_path)).regenerate_all()
    assert len(created)>0
    assert len(list((tmp_path/"components"/"axiolev").glob("*.tsx")))>=10

def test_regenerate_creates_tokens(tmp_path):
    UIRegenerator(str(tmp_path)).regenerate_all()
    tokens=tmp_path/"styles"/"axiolev-tokens.css"
    assert tokens.exists() and "#C9A961" in tokens.read_text()

def test_audit_improves_after_regen(tmp_path):
    n_before=sum(1 for f in UIAuditor(str(tmp_path)).audit() if f.severity in (Severity.VIOLATION,Severity.BLOCKER))
    UIRegenerator(str(tmp_path)).regenerate_all()
    n_after=sum(1 for f in UIAuditor(str(tmp_path)).audit() if f.severity in (Severity.VIOLATION,Severity.BLOCKER))
    assert n_after<n_before
