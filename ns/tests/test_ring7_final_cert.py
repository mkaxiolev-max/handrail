"""Ring 7 — Final Certification tests.

Phase D: verify required tags/branches exist, umbrella tag constant,
founder-grade tag format, and FinalCertResult certified state.
Tag: ring-7-final-cert-v1
"""
from __future__ import annotations

import datetime
import importlib


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestFinalCertConstants:
    def test_required_tags_is_list(self):
        from ns.services.canon.final_cert import REQUIRED_TAGS
        assert isinstance(REQUIRED_TAGS, list)

    def test_required_tags_contains_ncom_piic(self):
        from ns.services.canon.final_cert import REQUIRED_TAGS
        assert "ncom-piic-merged-v2" in REQUIRED_TAGS

    def test_required_tags_contains_ril_oracle(self):
        from ns.services.canon.final_cert import REQUIRED_TAGS
        assert "ril-oracle-merged-v2" in REQUIRED_TAGS

    def test_required_branches_is_list(self):
        from ns.services.canon.final_cert import REQUIRED_BRANCHES
        assert isinstance(REQUIRED_BRANCHES, list)

    def test_required_branches_contains_ncom_piic(self):
        from ns.services.canon.final_cert import REQUIRED_BRANCHES
        assert "feature/ncom-piic-v2" in REQUIRED_BRANCHES

    def test_required_branches_contains_ril_oracle(self):
        from ns.services.canon.final_cert import REQUIRED_BRANCHES
        assert "feature/ril-oracle-v2" in REQUIRED_BRANCHES

    def test_umbrella_tag_exact(self):
        from ns.services.canon.final_cert import UMBRELLA_TAG
        assert UMBRELLA_TAG == "ns-infinity-cqhml+ncom+ril-v1.0.0"

    def test_founder_grade_tag_prefix_value(self):
        from ns.services.canon.final_cert import FOUNDER_GRADE_TAG_PREFIX
        assert FOUNDER_GRADE_TAG_PREFIX == "ns-infinity-founder-grade-"


# ---------------------------------------------------------------------------
# founder_grade_tag()
# ---------------------------------------------------------------------------


class TestFounderGradeTag:
    def test_known_date(self):
        from ns.services.canon.final_cert import founder_grade_tag
        assert founder_grade_tag(datetime.date(2026, 4, 18)) == "ns-infinity-founder-grade-20260418"

    def test_starts_with_prefix(self):
        from ns.services.canon.final_cert import founder_grade_tag
        tag = founder_grade_tag(datetime.date(2026, 1, 1))
        assert tag.startswith("ns-infinity-founder-grade-")

    def test_suffix_is_8_digits(self):
        from ns.services.canon.final_cert import founder_grade_tag
        tag = founder_grade_tag(datetime.date(2026, 4, 18))
        suffix = tag[len("ns-infinity-founder-grade-"):]
        assert len(suffix) == 8
        assert suffix.isdigit()

    def test_no_arg_uses_today(self):
        from ns.services.canon.final_cert import founder_grade_tag
        tag = founder_grade_tag()
        today = datetime.date.today().strftime("%Y%m%d")
        assert tag == f"ns-infinity-founder-grade-{today}"


# ---------------------------------------------------------------------------
# verify_tags_exist()
# ---------------------------------------------------------------------------


class TestVerifyTagsExist:
    def test_returns_dict(self):
        from ns.services.canon.final_cert import verify_tags_exist
        result = verify_tags_exist(["ncom-piic-merged-v2", "ril-oracle-merged-v2"])
        assert isinstance(result, dict)

    def test_required_tags_all_present_in_repo(self):
        from ns.services.canon.final_cert import verify_tags_exist, REQUIRED_TAGS
        result = verify_tags_exist(REQUIRED_TAGS)
        missing = [t for t, ok in result.items() if not ok]
        assert missing == [], f"Missing tags in repo: {missing}"

    def test_nonexistent_tag_false(self):
        from ns.services.canon.final_cert import verify_tags_exist
        result = verify_tags_exist(["this-tag-does-not-exist-xyz-abc-999"])
        assert result["this-tag-does-not-exist-xyz-abc-999"] is False

    def test_default_keys_match_required_tags(self):
        from ns.services.canon.final_cert import verify_tags_exist, REQUIRED_TAGS
        result = verify_tags_exist()
        assert set(result.keys()) == set(REQUIRED_TAGS)


# ---------------------------------------------------------------------------
# verify_branches_exist()
# ---------------------------------------------------------------------------


class TestVerifyBranchesExist:
    def test_returns_dict(self):
        from ns.services.canon.final_cert import verify_branches_exist
        result = verify_branches_exist(["feature/ncom-piic-v2", "feature/ril-oracle-v2"])
        assert isinstance(result, dict)

    def test_required_branches_all_present_in_repo(self):
        from ns.services.canon.final_cert import verify_branches_exist, REQUIRED_BRANCHES
        result = verify_branches_exist(REQUIRED_BRANCHES)
        missing = [b for b, ok in result.items() if not ok]
        assert missing == [], f"Missing branches in repo: {missing}"

    def test_nonexistent_branch_false(self):
        from ns.services.canon.final_cert import verify_branches_exist
        result = verify_branches_exist(["feature/this-does-not-exist-xyz-999"])
        assert result["feature/this-does-not-exist-xyz-999"] is False

    def test_default_keys_match_required_branches(self):
        from ns.services.canon.final_cert import verify_branches_exist, REQUIRED_BRANCHES
        result = verify_branches_exist()
        assert set(result.keys()) == set(REQUIRED_BRANCHES)


# ---------------------------------------------------------------------------
# run_final_cert()
# ---------------------------------------------------------------------------


class TestRunFinalCert:
    def test_returns_final_cert_result(self):
        from ns.services.canon.final_cert import run_final_cert, FinalCertResult
        result = run_final_cert()
        assert isinstance(result, FinalCertResult)

    def test_certified_true(self):
        from ns.services.canon.final_cert import run_final_cert
        result = run_final_cert()
        assert result.certified is True

    def test_umbrella_tag_value(self):
        from ns.services.canon.final_cert import run_final_cert, UMBRELLA_TAG
        result = run_final_cert()
        assert result.umbrella_tag == UMBRELLA_TAG

    def test_founder_grade_tag_with_date(self):
        from ns.services.canon.final_cert import run_final_cert
        result = run_final_cert(datetime.date(2026, 4, 18))
        assert result.founder_grade_tag == "ns-infinity-founder-grade-20260418"

    def test_no_missing_tags(self):
        from ns.services.canon.final_cert import run_final_cert
        result = run_final_cert()
        assert result.missing_tags == []

    def test_no_missing_branches(self):
        from ns.services.canon.final_cert import run_final_cert
        result = run_final_cert()
        assert result.missing_branches == []

    def test_all_tags_verified_true(self):
        from ns.services.canon.final_cert import run_final_cert
        result = run_final_cert()
        assert all(result.tags_verified.values())

    def test_all_branches_verified_true(self):
        from ns.services.canon.final_cert import run_final_cert
        result = run_final_cert()
        assert all(result.branches_verified.values())


# ---------------------------------------------------------------------------
# Module interface
# ---------------------------------------------------------------------------


class TestFinalCertModuleInterface:
    def test_module_importable(self):
        mod = importlib.import_module("ns.services.canon.final_cert")
        assert mod is not None

    def test_has_run_final_cert(self):
        from ns.services.canon.final_cert import run_final_cert
        assert callable(run_final_cert)

    def test_has_verify_tags_exist(self):
        from ns.services.canon.final_cert import verify_tags_exist
        assert callable(verify_tags_exist)

    def test_has_verify_branches_exist(self):
        from ns.services.canon.final_cert import verify_branches_exist
        assert callable(verify_branches_exist)

    def test_has_founder_grade_tag(self):
        from ns.services.canon.final_cert import founder_grade_tag
        assert callable(founder_grade_tag)

    def test_has_final_cert_result_class(self):
        from ns.services.canon.final_cert import FinalCertResult
        assert FinalCertResult is not None
