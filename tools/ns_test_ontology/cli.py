from __future__ import annotations

import argparse
from pathlib import Path

from .ontology import build_ontology, discover_pytest_tests, score_from_ontology, write_reports


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--vitest-total", type=int, default=0)
    parser.add_argument("--xctest-files", type=int, default=0)
    args = parser.parse_args()

    out = Path(args.out)
    tests = discover_pytest_tests()
    ontology = build_ontology(tests)
    score = score_from_ontology(ontology, vitest_total=args.vitest_total, xctest_files=args.xctest_files)
    write_reports(out, ontology, score)

    print(f"pytest_total={ontology['total']}")
    print(f"unmapped={len(ontology['unmapped'])}")
    print(f"I7={ontology['instrument_totals'].get('I7', 0)}")
    print(f"I3={ontology['instrument_totals'].get('I3', 0)}")
    print(out / "TEST_ONTOLOGY_REPORT.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
