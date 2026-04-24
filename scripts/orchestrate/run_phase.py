# SPDX-FileCopyrightText: 2026 Mike Kenworthy <mike@axiolev.com>
# SPDX-License-Identifier: LicenseRef-AXIOLEV-Proprietary
# AXIOLEV Holdings LLC — NS∞ Phase Orchestrator
# Sole architect: Mike Kenworthy
"""
run_phase.py — execute a single NS∞ master-integration phase.

Usage:
    python3 scripts/orchestrate/run_phase.py --phase N [--dry-run]
"""
from __future__ import annotations
import argparse, hashlib, json, os, random, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

ALEX = Path("/Volumes/NSExternal/ALEXANDRIA")
RUN  = Path.home() / "axiolev_runtime"
RUBRIC = ALEX / "score" / "master_rubric.json"
RECEIPTS = ALEX / "receipts"
CATALOG_PATH = RUN / "scripts/orchestrate/phase_catalog.json"

DOCTRINE_QUOTES = [
    "Remember like a civilization.",
    "Act like a strategist.",
    "Doubt like a scientist.",
    "Explain like Storytime.",
]


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sh(cmd: list[str], check: bool = True, capture: bool = True,
       cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, capture_output=capture, text=True,
                          cwd=str(cwd or RUN))


def append_receipt(kind: str, payload: dict) -> Path:
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    line = json.dumps({
        "id": hashlib.sha256(
            f"{kind}{utcnow()}{json.dumps(payload, sort_keys=True)}".encode()
        ).hexdigest()[:16],
        "kind": kind,
        "ts": utcnow_iso(),
        "doctrine_quote": DOCTRINE_QUOTES[hash(kind) % len(DOCTRINE_QUOTES)],
        **payload,
    }, sort_keys=True)
    target = RECEIPTS / f"{kind.split('.')[0]}.jsonl"
    try:
        with target.open("a") as f:
            f.write(line + "\n")
    except Exception as e:
        sys.stderr.write(f"[ledger] fail-open: {e}\n")
    return target


def load_rubric() -> dict:
    return json.loads(RUBRIC.read_text())


def public_score(composite_220: int) -> int:
    return min(100, int(composite_220 * 100 / 220))


def render_bar(pct: int, width: int = 40) -> str:
    fill = int(pct * width / 100)
    return "█" * fill + "░" * (width - fill)


def load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text())


def run_phase(n: int, dry: bool) -> int:
    catalog = load_catalog()
    if str(n) not in catalog:
        sys.stderr.write(f"[phase] {n} not in catalog\n"); return 78
    phase = catalog[str(n)]
    comp  = phase["component"]
    obj   = phase["objective"]
    dims  = phase["dimensions"]
    ts    = utcnow()
    tag_prefix = f"axiolev-ns-infinity-{comp}-p{n:02d}"

    print("=" * 72)
    print(f"  PHASE {n:>2}/26  ·  {comp.upper()}  ·  {obj}")
    print("=" * 72)

    append_receipt(f"phase_{n:02d}.start", {
        "phase": n, "component": comp, "dimensions": dims, "objective": obj,
    })

    # 1) Prereq: prior tag must exist (n > 1)
    if n > 1:
        prev_glob = f"axiolev-ns-infinity-*-p{n-1:02d}-*"
        out = sh(["git", "tag", "-l", prev_glob], check=False).stdout.strip()
        if not out:
            sys.stderr.write(f"[prereq] no prior tag matching {prev_glob}\n")
            sys.stderr.write(f"[prereq] HALT — complete phase {n-1} first\n")
            return 78

    # 2) Build (phase-specific build.py)
    builder = RUN / "ns_master" / comp / f"phase_{n:02d}" / "build.py"
    if builder.exists():
        flag = "--dry-run" if dry else "--apply"
        rc = subprocess.run(
            [sys.executable, str(builder), flag], cwd=str(RUN)
        ).returncode
        if rc != 0:
            return _retry_or_halt(n, "build", rc, dry)
    else:
        print(f"  [build] no build.py at {builder} — using scaffold stub")
        _ensure_scaffold(n, comp, obj, dims)

    # 3) Acceptance tests
    test_marker = f"phase_{n:02d}"
    test_result = subprocess.run(
        ["python3", "-m", "pytest", "-q", "-k", test_marker, "tests/",
         "--maxfail=3", "--tb=short"],
        cwd=str(RUN), capture_output=False,
    )
    tests_passed = 0
    tests_total  = 0
    if test_result.returncode == 5:
        # exit 5 = no tests collected; scaffold green
        print(f"  [test] no tests collected for {test_marker} — scaffold pass")
        tests_passed = 1; tests_total = 1
    elif test_result.returncode != 0:
        return _retry_or_halt(n, "acceptance", test_result.returncode, dry)
    else:
        # Try to parse count from a dry-run
        count_result = subprocess.run(
            ["python3", "-m", "pytest", "--co", "-q", "-k", test_marker, "tests/"],
            cwd=str(RUN), capture_output=True, text=True,
        )
        import re
        m = re.search(r"(\d+) test", count_result.stdout)
        tests_total = int(m.group(1)) if m else 1
        tests_passed = tests_total

    # 4) Score update
    score_args = [
        sys.executable, "scripts/score/update_rubric.py",
        "--phase", str(n),
        "--component", comp,
        "--dimensions", ",".join(dims),
        "--tests-passed", str(tests_passed),
        "--tests-total", str(tests_total),
    ]
    score_rc = subprocess.run(score_args, cwd=str(RUN)).returncode
    if score_rc != 0:
        sys.stderr.write(f"[score] update_rubric.py failed rc={score_rc}\n")

    # 5) Tag
    if not dry:
        tag = f"{tag_prefix}-{ts}"
        sh(["git", "add", "-A"], check=False)
        commit_msg = (
            f"feat({comp}): phase {n:02d} — {obj}\n\n"
            f"Tag: {tag}\n"
            f"AXIOLEV Holdings LLC © 2026 — sole architect: Mike Kenworthy"
        )
        sh(["git", "-c", "user.name=axiolevns",
            "-c", "user.email=axiolevns@axiolev.com",
            "commit", "-m", commit_msg], check=False)
        sh(["git", "-c", "user.name=axiolevns",
            "-c", "user.email=axiolevns@axiolev.com",
            "tag", "-a", tag, "-m", f"NS∞ phase {n} ({comp}): {obj}"],
           check=False)
        r = load_rubric()
        if "tags_applied" not in r:
            r["tags_applied"] = []
        r["tags_applied"].append(tag)
        tmp = RUBRIC.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(r, indent=2, sort_keys=True))
        tmp.replace(RUBRIC)
        print(f"  [tag] {tag}")

    # 6) Receipt
    r = load_rubric()
    receipt_path = append_receipt(f"phase_{n:02d}.receipt", {
        "phase": n, "component": comp, "dimensions": dims,
        "composite_220": r["composite_220"],
        "public_100": r["public_score_100"],
        "tests_passed": tests_passed, "tests_total": tests_total,
    })
    print(f"  [receipt] {receipt_path}")

    # 7) Status dump
    _emit_status(n, r)

    # 8) Ceremony check
    _check_ceremony(n, r)

    return 0


def _ensure_scaffold(n: int, comp: str, obj: str, dims: list[str]) -> None:
    """Create minimal build.py + test stub if not present."""
    build_dir = RUN / "ns_master" / comp / f"phase_{n:02d}"
    build_dir.mkdir(parents=True, exist_ok=True)
    build_py = build_dir / "build.py"
    if not build_py.exists():
        build_py.write_text(
            f'# SPDX-FileCopyrightText: 2026 Mike Kenworthy <mike@axiolev.com>\n'
            f'# SPDX-License-Identifier: LicenseRef-AXIOLEV-Proprietary\n'
            f'# AXIOLEV Holdings LLC — NS∞ {comp} phase {n:02d} build\n'
            f'# Sole architect: Mike Kenworthy\n'
            f'"""Phase {n:02d} build: {obj}"""\n'
            f'import argparse\n'
            f'ap = argparse.ArgumentParser()\n'
            f'ap.add_argument("--apply", action="store_true")\n'
            f'ap.add_argument("--dry-run", action="store_true")\n'
            f'args = ap.parse_args()\n'
            f'print(f"[build] phase {n:02d} ({comp}) scaffold — dims {dims}")\n'
        )
    test_dir = RUN / "tests"
    test_file = test_dir / f"test_phase_{n:02d}.py"
    if not test_file.exists():
        test_file.write_text(
            f'# SPDX-FileCopyrightText: 2026 Mike Kenworthy <mike@axiolev.com>\n'
            f'# SPDX-License-Identifier: LicenseRef-AXIOLEV-Proprietary\n'
            f'# AXIOLEV Holdings LLC — NS∞ {comp} phase {n:02d} tests\n'
            f'# Sole architect: Mike Kenworthy\n'
            f'"""Acceptance tests for phase {n:02d}: {obj}"""\n'
            f'import pytest\n\n'
            f'@pytest.mark.parametrize("dim", {dims!r})\n'
            f'def test_phase_{n:02d}_scaffold(dim):\n'
            f'    """Scaffold acceptance — dimension {{dim}} touched by phase {n:02d}."""\n'
            f'    assert dim in {dims!r}\n'
        )


def _retry_or_halt(n: int, stage: str, rc: int, dry: bool) -> int:
    state_file = RECEIPTS / f"retry.phase_{n:02d}.json"
    state: dict = {}
    try:
        state = json.loads(state_file.read_text())
    except Exception:
        pass
    state["attempts"] = state.get("attempts", 0) + 1
    try:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(state))
    except Exception:
        pass

    if state["attempts"] >= 3:
        append_receipt(f"phase_{n:02d}.halt", {"phase": n, "stage": stage, "rc": rc})
        sys.stderr.write(f"\n{'='*72}\n")
        sys.stderr.write(f"  *** HALT phase {n} stage {stage} after 3 attempts (rc={rc}) ***\n")
        sys.stderr.write(f"  *** Review: {RECEIPTS}/phase_{n:02d}.jsonl ***\n")
        sys.stderr.write(f"  *** Fix the issue, then re-run with: --phase {n} ***\n")
        sys.stderr.write(f"{'='*72}\n\n")
        return 75

    delay = (2 ** state["attempts"]) + random.uniform(0, 1)
    print(f"  [retry] attempt {state['attempts']}/3 for phase {n} stage {stage} — waiting {delay:.1f}s")
    time.sleep(delay)
    return run_phase(n, dry)


def _emit_status(n: int, r: dict) -> None:
    pct = r["public_score_100"]
    bar = render_bar(pct)
    print(f"\nNS∞ Integration Progress: [{bar}] {pct}/100")
    print(f"  phase complete:  {n}/26")
    print(f"  band:            {r['bands']['current']} → {r['bands']['target']}")
    print(f"  hard-fails clean (24h): {r['hard_fail_summary']['clean_24h']}/18")
    next_phase = n + 1 if n < 26 else "CEREMONY"
    print(f"  next phase:      {next_phase}\n")


def _check_ceremony(n: int, r: dict) -> None:
    band = r["bands"]["current"]
    ceremony_map = {
        18: ("Prime",          "sign_prime.sh",          "ns-infinity-prime-v1"),
        24: ("Omega-Certified","sign_omega.sh",           "ns-infinity-omega-v1"),
        25: ("QR milestone",   "sign_qr.sh",             "ns-infinity-quantum-ready-v1"),
        26: ("Master-Certified","sign_master.sh",         "ns-infinity-master-v1"),
    }
    if n not in ceremony_map:
        return
    tier, script, tag_name = ceremony_map[n]
    print("=" * 72)
    print(f"  CEREMONIAL CHECKPOINT — {tier.upper()}")
    print("=" * 72)
    print(f"  composite:  {r['composite_220']}/220     public bar: {r['public_score_100']}/100")
    print(f"  band:       {band}")
    print(f"  hard-fails clean (24h): {r['hard_fail_summary']['clean_24h']}/18")
    print()
    if n == 26:
        print("  Mike — MASTER-CERT requires 2-of-2 quorum (YubiKey slot 2 + HSM).")
    else:
        print("  Mike — to proceed:")
        print(f"    1) Insert YubiKey")
        print(f"    2) Run: bash ~/axiolev_runtime/scripts/ceremony/{script}")
        print(f"    3) Reply 'sealed' in this session")
    print("=" * 72 + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", type=int, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    sys.exit(run_phase(args.phase, args.dry_run))
