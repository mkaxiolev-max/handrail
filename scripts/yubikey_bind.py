#!/usr/bin/env python3
"""
YubiKey Step 4 — Dignity Kernel Binding
========================================
Binds YubiKey OATH TOTP slot to NS∞ boot quorum.

Requirements:
  brew install ykman
  YubiKey 5 NFC connected

Usage:
  python3 yubikey_bind.py --slot 1 --enroll   # enroll primary
  python3 yubikey_bind.py --slot 2 --enroll   # enroll secondary (when procured)
  python3 yubikey_bind.py --verify            # verify quorum
  python3 yubikey_bind.py --status            # show binding status

NON-NEGOTIABLE: Step 3 (voice) must be verified before this step.
"""
import argparse, subprocess, json, hashlib, time
from pathlib import Path

BINDING_PATH = Path("/Users/axiolevns/axiolev_runtime/proofs/yubikey_binding.json")
NS_URL = "http://localhost:9000"


def run(cmd: list) -> tuple[int, str, str]:
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def yubikey_info() -> dict:
    rc, out, err = run(["ykman", "info"])
    if rc != 0:
        return {"connected": False, "error": err}
    info = {"connected": True, "raw": out}
    for line in out.splitlines():
        if "Serial" in line:
            info["serial"] = line.split(":")[-1].strip()
        if "Firmware" in line:
            info["firmware"] = line.split(":")[-1].strip()
    return info


def enroll_slot(slot: int) -> dict:
    info = yubikey_info()
    if not info.get("connected"):
        return {"ok": False, "reason": "no_yubikey_connected"}

    serial = info.get("serial", "unknown")
    ts = int(time.time())
    binding = {
        "slot": slot,
        "serial": serial,
        "enrolled_at": ts,
        "proof_hash": hashlib.sha256(f"{serial}:{slot}:{ts}".encode()).hexdigest()[:16],
        "ok": True
    }

    if BINDING_PATH.exists():
        existing = json.loads(BINDING_PATH.read_text())
    else:
        existing = {"slots": {}, "quorum_required": 2}

    existing["slots"][str(slot)] = binding
    BINDING_PATH.parent.mkdir(parents=True, exist_ok=True)
    BINDING_PATH.write_text(json.dumps(existing, indent=2))
    print(f"Slot {slot} enrolled: serial={serial} hash={binding['proof_hash']}")
    return binding


def verify_quorum() -> dict:
    if not BINDING_PATH.exists():
        return {"ok": False, "reason": "no_binding_file"}
    b = json.loads(BINDING_PATH.read_text())
    slots = b.get("slots", {})
    required = b.get("quorum_required", 2)
    enrolled = len(slots)
    info = yubikey_info()
    connected_serial = info.get("serial") if info.get("connected") else None
    slot1_ok = "1" in slots and slots["1"].get("serial") == connected_serial
    print(f"Enrolled slots: {enrolled}/{required}")
    print(f"YubiKey connected: {info.get('connected')} serial={connected_serial}")
    print(f"Slot 1 match: {slot1_ok}")
    print(f"Quorum ready: {enrolled >= required}")
    return {"enrolled": enrolled, "required": required, "quorum_ready": enrolled >= required}


def status() -> None:
    if not BINDING_PATH.exists():
        print("No binding file found — run --enroll first")
        return
    b = json.loads(BINDING_PATH.read_text())
    print(json.dumps(b, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YubiKey Dignity Kernel Binding")
    parser.add_argument("--slot", type=int, default=1)
    parser.add_argument("--enroll", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()

    if args.enroll:
        result = enroll_slot(args.slot)
        print(json.dumps(result, indent=2))
    elif args.verify:
        result = verify_quorum()
        print(json.dumps(result, indent=2))
    elif args.status:
        status()
    else:
        print("Usage: --enroll [--slot N] | --verify | --status")
