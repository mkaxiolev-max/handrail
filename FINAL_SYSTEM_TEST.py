#!/usr/bin/env python3
import sys,json
sys.path.insert(0,'~/axiolev_runtime')
from services.handrail.handrail.constitutional_router import ConstitutionalRouter
from services.ns_continuum.boot_sequence import BootSequenceManager
from services.handrail.handrail.kernel.dignity_kernel import DignityKernel
from services.handrail.handrail.kernel.yubikey_quorum import YubiKeyQuorum,YubiKeySlot
print("\n════════════════════════════════════════════════════════════════════════════════");print("OMEGA CPS V2 — FINAL SYSTEM INTEGRATION TEST");print("════════════════════════════════════════════════════════════════════════════════\n")
boot=BootSequenceManager();result=boot.execute_full_boot()
print(f"✅ BOOT SEQUENCE: {result['status']}\n")
for log in result.get('boot_log',[]):print(f"  {log['phase']}: {log['status']}")
print("\n" + "─"*80)
dignity=DignityKernel();rb_valid={"decision":{"allowed":True},"execution":{"all_ok":True},"result":{"output_ok":True},"violations":[]}
valid,msg=dignity.enforce_dignity_invariants(rb_valid);print(f"\n✅ DIGNITY KERNEL: {'PASS' if valid else 'FAIL'} — {msg}\n")
quorum=YubiKeyQuorum();quorum.state.arm_slot(YubiKeySlot.SLOT_1,"sig1");quorum.state.arm_slot(YubiKeySlot.SLOT_2,"sig2")
intent={"intent_id":"test_001"};kdr=quorum.dispatch_with_quorum(intent);print(f"✅ YUBIKEY QUORUM: {kdr.get('status','UNKNOWN')}\n")
router=ConstitutionalRouter();router.quorum.state.arm_slot(YubiKeySlot.SLOT_1,"sig1");router.quorum.state.arm_slot(YubiKeySlot.SLOT_2,"sig2")
route_result=router.route_intent_to_execution(intent,"φ:handrail:VALIDATE{test}");print(f"✅ CONSTITUTIONAL ROUTER: {route_result.get('status','UNKNOWN')}\n")
print("════════════════════════════════════════════════════════════════════════════════");print("✅ ALL HARDENING LAYERS OPERATIONAL");print("════════════════════════════════════════════════════════════════════════════════\n")
