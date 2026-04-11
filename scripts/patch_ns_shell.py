#!/usr/bin/env python3
"""
NS Shell Usage Audit
====================
Scans NS service Python files for subprocess/shell usage
and outputs a replacement map.

Run from repo root:
  python3 scripts/patch_ns_shell.py

Output:
  - Prints each file/line with shell usage
  - Classifies each as: REPLACE_WITH_CPS | REVIEW | SKIP
  - Writes ns_shell_audit.json
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

SCAN_ROOTS = [
    Path("services/ns"),
    Path("services/handrail"),
]

SHELL_PATTERNS = [
    "subprocess.run",
    "subprocess.call",
    "subprocess.Popen",
    "subprocess.check_output",
    "os.system",
    "os.popen",
    "shell=True",
]

# Ops that map directly to CPS typed ops
CPS_REPLACEMENTS = {
    "docker": "docker.compose_up / docker.compose_ps",
    "git status": "git.status",
    "git log": "git.log",
    "curl": "http.get",
    "ls": "fs.list",
    "cat": "fs.read",
    "pwd": "fs.pwd",
}


def classify(line: str) -> str:
    line_lower = line.lower()
    for keyword, cps_op in CPS_REPLACEMENTS.items():
        if keyword in line_lower:
            return f"REPLACE_WITH_CPS → {cps_op}"
    if "shell=True" in line:
        return "REPLACE_WITH_CPS → proc.run_allowed (or type-safe op)"
    return "REVIEW"


def scan_file(path: Path) -> list[dict]:
    findings = []
    try:
        lines = path.read_text().splitlines()
    except Exception:
        return findings

    for i, line in enumerate(lines, 1):
        for pattern in SHELL_PATTERNS:
            if pattern in line:
                findings.append({
                    "file": str(path),
                    "line": i,
                    "content": line.strip(),
                    "pattern": pattern,
                    "action": classify(line),
                })
                break
    return findings


def main() -> int:
    all_findings = []
    scanned = 0

    for root in SCAN_ROOTS:
        if not root.exists():
            print(f"[SKIP] {root} not found")
            continue
        for path in root.rglob("*.py"):
            if "__pycache__" in str(path):
                continue
            findings = scan_file(path)
            all_findings.extend(findings)
            scanned += 1

    # Print
    print(f"\n=== NS Shell Audit ===")
    print(f"Scanned: {scanned} Python files")
    print(f"Found:   {len(all_findings)} shell usage sites\n")

    replace_count = 0
    review_count = 0

    for f in all_findings:
        action = f["action"]
        marker = "🔴" if "REPLACE" in action else "🟡"
        print(f"{marker} {f['file']}:{f['line']}")
        print(f"   {f['content']}")
        print(f"   → {action}\n")
        if "REPLACE" in action:
            replace_count += 1
        else:
            review_count += 1

    print(f"Summary: {replace_count} to replace with CPS, {review_count} to review")

    # Write JSON
    out = Path("ns_shell_audit.json")
    out.write_text(json.dumps(all_findings, indent=2))
    print(f"\nAudit written to: {out}")

    return 0 if len(all_findings) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
