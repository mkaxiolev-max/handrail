import pathlib, tempfile, pytest
from services.aletheia_control import receipts as R

@pytest.fixture
def tmp_log():
    p = pathlib.Path(tempfile.mkstemp(suffix=".jsonl")[1]); p.write_text(""); yield p; p.unlink(missing_ok=True)

def test_append_and_verify_chain(tmp_log):
    for i in range(5):
        R.append(tmp_log, "ALET_CONTROL_CLASSIFICATION_RECEIPT", {"i": i})
    assert R.verify(tmp_log) is True

def test_tamper_breaks_chain(tmp_log):
    R.append(tmp_log, "ALET_CONTROL_CLASSIFICATION_RECEIPT", {"i": 1})
    R.append(tmp_log, "ALET_CONTROL_CLASSIFICATION_RECEIPT", {"i": 2})
    lines = tmp_log.read_text().splitlines()
    lines[0] = lines[0].replace('"i": 1', '"i": 99')
    tmp_log.write_text("\n".join(lines)+"\n")
    assert R.verify(tmp_log) is False

def test_unknown_kind_rejected(tmp_log):
    with pytest.raises(ValueError):
        R.append(tmp_log, "BOGUS", {})
