import argparse
import json
from .archivist import Archivist

def main():
    p = argparse.ArgumentParser(prog="handrail", description="Handrail CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("boot")
    b.add_argument("--strict", action="store_true")

    d = sub.add_parser("doctor")
    d.add_argument("--integrity-check", action="store_true")

    v = sub.add_parser("validate")
    v.add_argument("--full", action="store_true")

    rep = sub.add_parser("repair")
    rep.add_argument("--session", required=True)

    a = sub.add_parser("append-demo")
    a.add_argument("--session", default="demo_session")

    r = sub.add_parser("replay")
    r.add_argument("--session", required=True)
    r.add_argument("--limit", type=int, default=200)

    s = sub.add_parser("serve")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8011)

    args = p.parse_args()
    arch = Archivist()

    if args.cmd == "boot":
        out = arch.boot(strict=args.strict)
    elif args.cmd == "doctor":
        out = arch.doctor(integrity_check=args.integrity_check)
    elif args.cmd == "validate":
        out = arch.validate_lineage(full=args.full)
    elif args.cmd == "repair":
        out = arch.repair_fork(args.session)
    elif args.cmd == "append-demo":
        res = arch.append_batch([
            {"actor_id": "demo", "session_id": args.session, "kind": "session_start", "payload_json": {"context": "demo"}, "idempotency_key": "start"},
            {"actor_id": "demo", "session_id": args.session, "kind": "turn_complete", "payload_json": {"input": "hello", "output": "world"}, "idempotency_key": "turn1"},
        ])
        out = {"append": res.__dict__}
    elif args.cmd == "replay":
        rows = arch.read(args.session, limit=args.limit)
        out = {"session_id": args.session, "receipts": list(reversed(rows))}
    elif args.cmd == "serve":
        import uvicorn
        uvicorn.run("handrail.server:app", host=args.host, port=args.port, reload=False)
        return
    else:
        out = {"error": "unknown_command"}

    print(json.dumps(out, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
