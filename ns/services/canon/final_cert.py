"""Final Certification — Ring 7 (Phase D).

Verifies readiness gating for ns-infinity certification.
Tags: ncom-piic-merged-v2, ril-oracle-merged-v2.
Branches: feature/ncom-piic-v2, feature/ril-oracle-v2.
"""
from __future__ import annotations

import datetime
import subprocess
from dataclasses import dataclass, field
from typing import Optional

REQUIRED_TAGS: list[str] = ["ncom-piic-merged-v2", "ril-oracle-merged-v2"]
REQUIRED_BRANCHES: list[str] = ["feature/ncom-piic-v2", "feature/ril-oracle-v2"]
UMBRELLA_TAG: str = "ns-infinity-cqhml+ncom+ril-v1.0.0"
FOUNDER_GRADE_TAG_PREFIX: str = "ns-infinity-founder-grade-"


def founder_grade_tag(date: Optional[datetime.date] = None) -> str:
    """Return the founder-grade tag name for the given date (default: today)."""
    d = date or datetime.date.today()
    return f"{FOUNDER_GRADE_TAG_PREFIX}{d.strftime('%Y%m%d')}"


def _git_tags() -> list[str]:
    result = subprocess.run(["git", "tag"], capture_output=True, text=True)
    return [t.strip() for t in result.stdout.splitlines() if t.strip()]


def _git_branches() -> set[str]:
    result = subprocess.run(["git", "branch", "-a"], capture_output=True, text=True)
    normalized: set[str] = set()
    for line in result.stdout.splitlines():
        # Strip leading whitespace, *, + (worktree marker), spaces
        name = line.strip().lstrip("*+ ").strip()
        normalized.add(name)
        # Also add short name stripped of remotes/origin/ prefix
        if name.startswith("remotes/origin/"):
            normalized.add(name[len("remotes/origin/"):])
    return normalized


def verify_tags_exist(required: Optional[list[str]] = None) -> dict[str, bool]:
    """Return {tag: exists} for each required tag."""
    tags = required if required is not None else REQUIRED_TAGS
    existing = set(_git_tags())
    return {t: t in existing for t in tags}


def verify_branches_exist(required: Optional[list[str]] = None) -> dict[str, bool]:
    """Return {branch: exists} for each required branch."""
    branches = required if required is not None else REQUIRED_BRANCHES
    existing = _git_branches()
    return {br: br in existing for br in branches}


@dataclass
class FinalCertResult:
    tags_verified: dict[str, bool]
    branches_verified: dict[str, bool]
    umbrella_tag: str
    founder_grade_tag: str
    certified: bool
    missing_tags: list[str] = field(default_factory=list)
    missing_branches: list[str] = field(default_factory=list)


def run_final_cert(date: Optional[datetime.date] = None) -> FinalCertResult:
    """Run the final certification check (read-only; does not emit git tags)."""
    tags_result = verify_tags_exist()
    branches_result = verify_branches_exist()
    missing_tags = [t for t, ok in tags_result.items() if not ok]
    missing_branches = [br for br, ok in branches_result.items() if not ok]
    certified = not missing_tags and not missing_branches
    return FinalCertResult(
        tags_verified=tags_result,
        branches_verified=branches_result,
        umbrella_tag=UMBRELLA_TAG,
        founder_grade_tag=founder_grade_tag(date),
        certified=certified,
        missing_tags=missing_tags,
        missing_branches=missing_branches,
    )
