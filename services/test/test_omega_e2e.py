import sys,json
sys.path.insert(0,'~/axiolev_runtime')
from services.handrail.handrail.voice.twilio_dispatcher import TwilioVoiceHandler
from services.handrail.handrail.ns_continuum_bridge import NSContinuumBridge
from services.handrail.handrail.kernel.policy_ledger import PolicyObject,PolicyLedger
from services.handrail.handrail.kernel.algebraic_gates_engine import AlgebraicGatesEngine
class MockKDRHandler:
 def dispatch_with_receipt(self,intent):return{"receipt_id":f"kdr_{intent.get('intent_id')}","allowed":True,"timestamp":"2026-03-26T00:00:00Z"}
class MockExecutor:
 def execute(self,kdr):return{"status":"SUCCESS","result":{"summary":"Test operation completed"},"timestamp":"2026-03-26T00:00:00Z"}
class OmegaE2ETest:
 def __init__(self):self.voice=TwilioVoiceHandler();self.bridge=NSContinuumBridge();self.gates=AlgebraicGatesEngine();self.ledger=PolicyLedger();self.kdr=MockKDRHandler();self.executor=MockExecutor()
 def test_voice_to_response(self):r,rb=self.voice.full_pipeline("+1234567890","test message","sms",self.kdr,self.executor);assert rb.get('status')=="SUCCESS";print("✅ test_voice_to_response PASSED")
 def test_handrail_to_ns_bridge(self):kdr=self.kdr.dispatch_with_receipt({"intent_id":"test_intent"});result=self.bridge.full_bridge_pipeline(kdr,{"intent_id":"test_intent"});assert result.get('status')=="SUCCESS";print("✅ test_handrail_to_ns_bridge PASSED")
 def test_gates_validation(self):inst="φ:handrail:VALIDATE{test}";result=self.gates.execute_all_gates(inst);assert result.get('status')=="ACCEPTED";assert result.get('gates_passed')==6;print("✅ test_gates_validation PASSED")
 def test_policy_ledger(self):p=PolicyObject("handrail",["rule1","rule2"]);s,h=self.ledger.append_policy(p);assert s==True;assert h==p.content_hash;print("✅ test_policy_ledger PASSED")
 def run_all(self):self.test_voice_to_response();self.test_handrail_to_ns_bridge();self.test_gates_validation();self.test_policy_ledger();print("\n════════════════════════════════════════════════════════════════════════════════");print("✅ ALL E2E TESTS PASSED");print("════════════════════════════════════════════════════════════════════════════════")
if __name__=="__main__":t=OmegaE2ETest();t.run_all()
