"""
handrail CLI — Phase 1
Usage: python -m handrail.cli.main <command> [args]
Or alias: handrail <command> [args]
"""

from __future__ import annotations

import argparse
import json
import sys

from handrail.cli.cps import (
    cat_cps,
    inspect_run,
    list_cps,
    list_policies,
    logs_run,
    replay_run,
    run_cps,
)
from handrail.cli.doctor import doctor


def _print_json(obj: dict) -> None:
    print(json.dumps(obj, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="handrail",
        description="Handrail — deterministic AI execution control plane",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # handrail doctor
    sub.add_parser("doctor", help="Check system readiness")

    # handrail cps <subcommand>
    cps_p = sub.add_parser("cps", help="CPS operations")
    cps_sub = cps_p.add_subparsers(dest="cps_command", required=True)
    cps_sub.add_parser("list", help="List available CPS plans")
    cat_p = cps_sub.add_parser("cat", help="Print a CPS plan")
    cat_p.add_argument("cps_id")
    run_p = cps_sub.add_parser("run", help="Execute a CPS plan")
    run_p.add_argument("cps_id")
    run_p.add_argument("--api", default="http://127.0.0.1:8011", help="Handrail API base URL")
    run_p.add_argument("--json", dest="raw_json", action="store_true", help="Print full JSON result")

    # handrail inspect <run_id>
    inspect_p = sub.add_parser("inspect", help="Inspect a CPS run")
    inspect_p.add_argument("run_id")

    # handrail replay <run_id>
    replay_p = sub.add_parser("replay", help="Replay a CPS run and compare digest")
    replay_p.add_argument("run_id")
    replay_p.add_argument("--api", default="http://127.0.0.1:8011")

    # handrail logs <run_id>
    logs_p = sub.add_parser("logs", help="Print logs for a CPS run")
    logs_p.add_argument("run_id")
    logs_p.add_argument("--full", action="store_true", help="Print full cps_result.json")

    # handrail policy list
    policy_p = sub.add_parser("policy", help="Policy operations")
    policy_sub = policy_p.add_subparsers(dest="policy_command", required=True)
    policy_sub.add_parser("list", help="List available policy profiles")

    args = parser.parse_args(argv)

    if args.command == "doctor":
        result = doctor()
        _print_json(result)
        return 0 if result["ok"] else 1

    if args.command == "cps":
        if args.cps_command == "list":
            for cps_id in list_cps():
                print(cps_id)
            return 0
        if args.cps_command == "cat":
            plan = cat_cps(args.cps_id)
            _print_json(plan)
            return 0
        if args.cps_command == "run":
            result = run_cps(args.cps_id, api_base=args.api)
            if getattr(args, "raw_json", False):
                _print_json(result)
            else:
                # Compressed summary
                summary = {
                    "cps_id": result.get("cps_id"),
                    "ok": result.get("ok"),
                    "run_id": result.get("run_id"),
                    "run_dir": result.get("run_dir"),
                    "results": result.get("results"),
                    "policy_profile": result.get("policy_profile"),
                    "metrics": result.get("metrics"),
                    "expect_passed": result.get("expect_result", {}).get("passed"),
                    "result_digest": result.get("result_digest", "")[:16] + "...",
                }
                _print_json(summary)
            return 0 if result.get("ok") else 1

    if args.command == "inspect":
        result = inspect_run(args.run_id)
        _print_json(result)
        return 0

    if args.command == "replay":
        result = replay_run(args.run_id, api_base=args.api)
        _print_json(result)
        return 0 if result.get("match") else 1

    if args.command == "logs":
        logs_run(args.run_id, full=getattr(args, "full", False))
        return 0

    if args.command == "policy":
        if args.policy_command == "list":
            for name in list_policies():
                print(name)
            return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
