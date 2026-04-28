"""C22 — Architecture validator tests. I8."""
from pathlib import Path
from tools.architecture_validator.validator import ArchitectureValidator, ValidationCheck


def test_validator_runs(tmp_path):
    v = ArchitectureValidator(root=tmp_path)
    results = v.run()
    assert len(results) == 100


def test_all_checks_are_validation_check(tmp_path):
    v = ArchitectureValidator(root=tmp_path)
    for r in v.run():
        assert isinstance(r, ValidationCheck)


def test_score_0_to_100(tmp_path):
    v = ArchitectureValidator(root=tmp_path)
    s = v.score()
    assert 0.0 <= s <= 100.0


def test_real_root_scores_higher():
    real_root = Path("/Users/axiolevns/axiolev_runtime")
    v = ArchitectureValidator(root=real_root)
    s = v.score()
    assert s > 50.0


def test_failed_checks_list(tmp_path):
    v = ArchitectureValidator(root=tmp_path)
    v.run()
    failed = v.failed_checks()
    assert isinstance(failed, list)


def test_check_ids_1_to_100(tmp_path):
    v = ArchitectureValidator(root=tmp_path)
    ids = {r.id for r in v.run()}
    assert min(ids) == 1
    assert max(ids) == 100
