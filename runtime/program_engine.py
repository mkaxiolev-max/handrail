"""
Program Runtime Engine — the single shared substrate for all 10 programs.
One runtime. One receipt model. One policy model. One role model. Many program tables.
When tempted to add custom behavior for one program: is this a state rule or a new engine primitive?
"""
import json, hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from runtime.state_resolver import StateResolver
from runtime.role_router import RoleRouter
from runtime.memory_scope import MemoryScope
from runtime.whisper_generator import WhisperGenerator
from runtime.receipt_writer import ReceiptWriter

PROGRAM_RUNS = Path("/Volumes/NSExternal/.run/program_runs")

def ts(): return datetime.now(timezone.utc).isoformat()
def prid(s): return f"prg_{hashlib.sha256((s+ts()).encode()).hexdigest()[:10]}"

class ProgramEngine:
    def __init__(self):
        self.state_resolver = StateResolver()
        self.role_router = RoleRouter()
        self.memory_scope = MemoryScope()
        self.whisper_gen = WhisperGenerator()
        self.receipt_writer = ReceiptWriter()

    def start(self, program_id: str, context: dict = None) -> dict:
        """program.start — create a new governed program runtime."""
        lib = Path(__file__).parent.parent / "programs" / "program_library_v1.json"
        programs = json.loads(lib.read_text())["programs"] if lib.exists() else []
        prog_def = next((p for p in programs if p["program_id"] == program_id), None)
        if not prog_def:
            raise ValueError(f"Program {program_id} not in library")

        first_state = prog_def["states"][0]
        run_id = prid(program_id)
        runtime = {
            "program_id": program_id,
            "program_run_id": run_id,
            "state": first_state,
            "active_role": self.role_router.get_default_role(first_state),
            "policy_bundle": prog_def.get("policy_bundle", f"{program_id}_policy_v1"),
            "context": context or {},
            "receipts": [],
            "created_at": ts(),
            "updated_at": ts(),
        }

        # Persist
        PROGRAM_RUNS.mkdir(parents=True, exist_ok=True)
        with open(PROGRAM_RUNS / f"{run_id}.json", "w") as f:
            json.dump(runtime, f, indent=2)

        print(f"  [program.start] {program_id} | run={run_id} | state={first_state} | role={runtime['active_role']}")
        return runtime

    def advance_state(self, runtime: dict, trigger: str, proposed_next: Optional[str] = None,
                      actions: list = None, risk_flags: list = None) -> dict:
        """program.advance_state — validated, receipted, ledger-ratified."""
        # Resolve canonical current state from ledger
        resolution = self.state_resolver.resolve(runtime)
        current = resolution["canonical_state"]

        # Use proposed_next or auto-advance
        next_state = proposed_next or resolution.get("next_state")
        if not next_state:
            raise ValueError(f"No next state available from {current}")

        # Validate the transition
        validation = self.state_resolver.validate_transition(runtime, next_state, trigger)
        if not validation["valid"]:
            raise ValueError(f"Invalid transition: {validation['reason']}")

        # Route role for new state
        routing = self.role_router.route(next_state, trigger)
        new_role = routing["selected_role"]
        handoff = self.role_router.get_handoff(runtime["active_role"], new_role, next_state)

        # Write transition receipt
        receipt = self.receipt_writer.write_transition(
            program_runtime=runtime,
            prior_state=current,
            next_state=next_state,
            trigger=trigger,
            active_role=new_role,
            actions_executed=actions or [f"program.advance_state:{current}→{next_state}"],
            risk_flags=risk_flags or [],
            next_state_patch={"state": next_state, "active_role": new_role},
            memory_update_intent=[f"update_state_{next_state}"],
        )

        # Persist updated runtime
        self._persist(runtime)

        print(f"  [program.advance_state] {current} → {next_state} | role={new_role} | trigger={trigger}")
        if handoff:
            print(f"  [HANDOFF] {handoff}")

        return {"runtime": runtime, "receipt": receipt, "handoff": handoff}

    def route_role(self, runtime: dict, trigger: Optional[str] = None) -> dict:
        """program.route_role — deterministic role selection."""
        state = runtime["state"]
        routing = self.role_router.route(state, trigger)
        token = self.role_router.acquire_speaker_token(runtime["program_run_id"], routing["selected_role"])
        print(f"  [program.route_role] state={state} trigger={trigger} → role={routing['selected_role']} basis={routing['routing_basis']}")
        return {"routing": routing, "speaker_token": token}

    def capture_signal(self, runtime: dict, signal_type: str, signal_data: dict) -> dict:
        """program.capture_signal — log incoming signal for state resolver."""
        sig = {"signal_type": signal_type, "data": signal_data,
               "program_run_id": runtime["program_run_id"],
               "state_at_capture": runtime["state"], "timestamp": ts()}
        sig_path = PROGRAM_RUNS / f"{runtime['program_run_id']}_signals.jsonl"
        with open(sig_path, "a") as f:
            f.write(json.dumps(sig) + "\n")
        return sig

    def generate_whisper(self, runtime: dict, trigger: Optional[str] = None,
                         prospect_signal: str = "") -> dict:
        """program.generate_whisper — NS whispers to operator."""
        return self.whisper_gen.generate(runtime, trigger, prospect_signal)

    def assemble_role_context(self, runtime: dict, role: Optional[str] = None) -> dict:
        """Assemble memory-scoped context for a role."""
        target_role = role or runtime["active_role"]
        return self.memory_scope.assemble_context(target_role, runtime["context"])

    def _persist(self, runtime: dict):
        PROGRAM_RUNS.mkdir(parents=True, exist_ok=True)
        with open(PROGRAM_RUNS / f"{runtime['program_run_id']}.json", "w") as f:
            json.dump(runtime, f, indent=2)

    def load(self, run_id: str) -> Optional[dict]:
        path = PROGRAM_RUNS / f"{run_id}.json"
        if path.exists():
            return json.loads(path.read_text())
        return None
