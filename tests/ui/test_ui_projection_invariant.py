"""UI never defines truth — projection invariant test."""
import os

UI_DIR = os.path.join(os.path.dirname(__file__), "../../ns_ui/violet_panel")

FORBIDDEN = [
    "Math.random",
    "fake",
    "mock",
    "placeholder",
    "TODO: data",
    "hardcoded",
]


def _all_js_files():
    for root, _, files in os.walk(UI_DIR):
        for f in files:
            if f.endswith((".jsx", ".js", ".tsx", ".ts")):
                yield os.path.join(root, f)


def test_ui_never_defines_truth():
    violations = []
    for fpath in _all_js_files():
        with open(fpath) as f:
            content = f.read()
        for term in FORBIDDEN:
            if term in content:
                violations.append(f"{fpath}: contains '{term}'")
    assert violations == [], "UI projection invariant violated:\n" + "\n".join(violations)


def test_all_data_via_fetch():
    """All data in UI components must come from fetch() calls."""
    for fpath in _all_js_files():
        fname = os.path.basename(fpath)
        if fname in ("api.js", "error.js", "vite.config.js"):
            continue
        with open(fpath) as f:
            content = f.read()
        if "ENDPOINTS" in content or "fetchEndpoint" in content:
            assert "fetch" in content or "fetchEndpoint" in content, \
                f"{fname} uses ENDPOINTS but no fetch call found"
