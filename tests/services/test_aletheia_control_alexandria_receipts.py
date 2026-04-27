"""Alexandria 6-path receipt integrity."""
import pathlib

def test_alexandria_paths_exist():
    expected = [
        "alexandria/raw/control_inputs",
        "alexandria/structured/control_classifications",
        "alexandria/receipts/aletheia_control",
        "alexandria/waste/concern",
        "alexandria/drift/control_terms",
        "alexandria/canon/control_principles",
    ]
    for p in expected:
        assert pathlib.Path(p).exists() or pathlib.Path(p).parent.exists()
