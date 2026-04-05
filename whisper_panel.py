#!/usr/bin/env python3
"""
Whisper Panel — terminal cockpit for live program operation.
Not a chatbot. A cockpit. NS whispers, human executes.
Run: python3 whisper_panel.py [program_id] [--new|--load run_id]
"""
import sys, json, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from runtime.program_engine import ProgramEngine

def clear(): os.system("clear")

def render_panel(runtime: dict, packet: dict = None):
    clear()
    state = runtime["state"]
    role = runtime["active_role"]
    run_id = runtime["program_run_id"]
    prog = runtime["program_id"]

    print("╔══════════════════════════════════════════════════════════╗")
    print("║           NS∞ WHISPER PANEL — FOUNDER COCKPIT           ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"  Program:  {prog}")
    print(f"  Run ID:   {run_id}")
    print(f"  State:    {state}")
    print(f"  Role:     {role}")
    print(f"  Receipts: {len(runtime.get('receipts',[]))}")
    print("─"*62)

    if packet:
        risk_icon = {"LOW":"◻","MEDIUM":"◈","HIGH":"◆","CRITICAL":"⬛"}.get(packet.get("risk","LOW"),"?")
        print(f"  SIGNAL   {packet.get('signal','')}")
        print(f"  RISK     {risk_icon} {packet.get('risk','?')}")
        print(f"  MOVE     {packet.get('move','')}")
        print(f"  LINE     » {packet.get('suggested_line','')}")
        if packet.get("handoff"):
            print(f"  HANDOFF  ⇒ {packet['handoff']}")
        pol = packet.get("policy_result", {})
        if pol.get("violations"):
            print(f"  POLICY   ✗ {' | '.join(pol['violations'][:2])}")
        else:
            print(f"  POLICY   ✓ ALLOW")
        print(f"  APPROVED {'✓ YES' if packet.get('approved') else '✗ NO — policy blocked'}")
    print("─"*62)
    print("  Commands: [a]dvance  [r]oute  [w]hisper  [s]ignal  [q]uit")
    print("─"*62)

def main():
    engine = ProgramEngine()
    prog_id = sys.argv[1] if len(sys.argv) > 1 else "commercial_cps_program_v1"

    if "--load" in sys.argv:
        idx = sys.argv.index("--load")
        run_id = sys.argv[idx+1]
        runtime = engine.load(run_id)
        if not runtime:
            print(f"Run {run_id} not found.")
            sys.exit(1)
        print(f"Loaded run: {run_id}")
    else:
        prospect = input(f"Starting {prog_id}. Prospect name (or Enter to skip): ").strip()
        runtime = engine.start(prog_id, {"prospect": prospect} if prospect else {})

    packet = engine.generate_whisper(runtime)
    render_panel(runtime, packet)

    while True:
        cmd = input("\nCommand > ").strip().lower()
        if cmd == "q":
            print("Session ended. Run ID:", runtime["program_run_id"])
            break
        elif cmd == "a":
            trigger = input("Trigger (or Enter for auto): ").strip() or None
            try:
                result = engine.advance_state(runtime, trigger=trigger or "manual_advance")
                runtime = result["runtime"]
                packet = engine.generate_whisper(runtime, trigger)
                render_panel(runtime, packet)
            except Exception as e:
                print(f"  ✗ {e}")
        elif cmd == "r":
            trigger = input("Trigger for routing: ").strip() or None
            result = engine.route_role(runtime, trigger)
            print(f"  → Role: {result['routing']['selected_role']} (basis: {result['routing']['routing_basis']})")
        elif cmd == "w":
            trigger = input("Trigger (or Enter for default): ").strip() or None
            signal = input("Prospect signal: ").strip()
            packet = engine.generate_whisper(runtime, trigger, signal)
            render_panel(runtime, packet)
        elif cmd == "s":
            sig_type = input("Signal type: ").strip()
            sig_data = input("Signal data (or Enter): ").strip()
            engine.capture_signal(runtime, sig_type, {"raw": sig_data})
            print(f"  Signal logged: {sig_type}")
        else:
            print("  Unknown command.")

if __name__ == "__main__":
    main()
