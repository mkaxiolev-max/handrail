"""
Dignity Kernel — Hamiltonian Execution Gate
Constitutional gate. Precedence: DK > Canon > PolicyBundle > RoleBinding > heuristics.
Never-events require YubiKey quorum amendment to modify.
"""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

NEVER_EVENTS = {
    "system.delete_all","system.wipe","system.format_disk",
    "alexandria.delete_ledger","alexandria.truncate",
    "identity.impersonate_founder","identity.revoke_all_keys",
    "dignity.disable_kernel","dignity.bypass",
    "quorum.dissolve","policy.delete_all","data.exfiltrate",
    "auth.revoke_all","governance.bypass_ratification",
    "schema.overwrite_without_quorum",
}

OP_DIGNITY = {
    "http.get":1.0,"http.post":0.9,"docker.compose_up":1.0,"docker.compose_ps":1.0,
    "docker.compose_down":0.9,"system.health_check":1.0,"fs.read_file":1.0,
    "fs.list_dir":1.0,"fs.write_file":0.85,"git.status":1.0,"git.log":1.0,
    "twilio.send_sms":0.8,"twilio.voice_call":0.8,
    "program.start":1.0,"program.advance_state":0.9,"program.route_role":0.9,
    "program.generate_whisper":0.95,"program.log_receipt":1.0,
    "program.capture_signal":0.9,"program.flag_risk":1.0,
    "deal.set_heat_score":0.9,"deal.capture_objection":0.9,
    "deal.record_pricing_signal":0.85,"deal.assign_owner":0.85,
    "comms.send_intro":0.8,"comms.send_update":0.8,
    "governance.draft_amendment":0.7,"governance.request_quorum":0.7,
    "governance.ratify_amendment":0.65,"governance.deploy_policy":0.65,
    "fs.delete_file":0.6,"system.exec_shell":0.5,
    "auth.revoke_key":0.4,"policy.update_rule":0.5,
    "alexandria.append":0.9,
}
ETA, BETA, H_BLOCK = 0.85, 1.2, 0.35

def _ts(): return datetime.now(timezone.utc).isoformat()
def _sha(s): return hashlib.sha256(s.encode()).hexdigest()[:12]

class DignityKernel:
    def __init__(self, ledger_path=None):
        self.ledger_path = Path(ledger_path) if ledger_path else None

    def _h(self, op, ctx):
        vd = OP_DIGNITY.get(op, 0.75)
        if ctx.get("elevated_risk"): vd *= (1.0/BETA)
        ve = 1.0 if op in OP_DIGNITY else 0.85
        return round(ETA*vd + (1-ETA)*ve, 4), round(vd, 4)

    def check(self, op, args, ctx=None):
        ctx = ctx or {}
        t = _ts()
        did = f"DK-{_sha(op+t)}"
        ah = _sha(json.dumps(args, sort_keys=True))
        if op in NEVER_EVENTS:
            d = {"decision_id":did,"op":op,"args_hash":ah,"hamiltonian_score":0.0,
                 "dignity_potential":0.0,"result":"BLOCKED",
                 "never_event_triggered":op,
                 "reason":f"NEVER_EVENT: {op} constitutionally blocked","timestamp":t}
            self._log(d); return d
        h, vd = self._h(op, ctx)
        result = "PASS" if h >= H_BLOCK else "BLOCKED"
        d = {"decision_id":did,"op":op,"args_hash":ah,"hamiltonian_score":h,
             "dignity_potential":vd,"result":result,"never_event_triggered":None,
             "reason":f"H={h} {'≥' if result=='PASS' else '<'} {H_BLOCK}","timestamp":t}
        self._log(d); return d

    def gate(self, op, args, ctx=None):
        d = self.check(op, args, ctx); return d["result"]=="PASS", d

    def _log(self, d):
        if self.ledger_path:
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.ledger_path,"a") as f: f.write(json.dumps(d)+"\n")

_inst = None
def get_kernel(ledger_path=None):
    global _inst
    if _inst is None: _inst = DignityKernel(ledger_path)
    return _inst
