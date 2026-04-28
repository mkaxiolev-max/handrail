"""v10 — Symphony OS import boundary CI gate."""
import pathlib, re, pytest

def test_no_symphony_imports_in_lenses():
    root = pathlib.Path("services/ns/nss/lenses")
    if not root.exists():
        pytest.skip("Lenses directory not found in CWD — run from $RUNTIME")
    bad = []
    for p in root.rglob("*.py"):
        if "contracts_external" in p.parts: continue
        text = p.read_text()
        if re.search(r"\bfrom\s+symphony_os\b|\bimport\s+symphony_os\b", text):
            bad.append(str(p))
    assert not bad, f"Symphony coupling violation: {bad}"

def test_symphony_contracts_no_symphony_import():
    path = pathlib.Path(
        "services/ns/nss/lenses/contracts_external/symphony_contracts.py")
    if not path.exists():
        pytest.skip("symphony_contracts.py not found")
    text = path.read_text()
    # Check for actual import statements only (line-anchored) — docstring mentions are fine
    assert not re.search(r"^\s*(from\s+symphony_os|import\s+symphony_os)\b", text, re.MULTILINE), \
        "symphony_contracts.py must not import from symphony_os"
