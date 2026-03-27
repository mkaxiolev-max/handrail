import json
from typing import Dict,Any
from enum import Enum
class ABIVersion(Enum):
 INTENT_V1="IntentPacket.v1"
 CPS_V1="CPSPacket.v1"
 KDR_V1="KernelDecisionReceipt.v1"
 COMPUTE_RECEIPT_V1="ComputeReceipt.v1"
 PROOF_RECEIPT_V1="ProofReceipt.v1"
 RETURN_BLOCK_V3="ReturnBlock.v3"
 ADAPTER_CONTRACT_V1="AdapterContract.v1"
class ABIValidator:
 REQUIRED_FIELDS={
  "IntentPacket.v1":["version","intent","args","constraints","idempotency_key","caller_id","session_id","timestamp"],
  "CPSPacket.v1":["version","objective","policy_profile","ops","expect","risk_tier","mission_graph_id"],
  "KernelDecisionReceipt.v1":["allowed","receipt_id"],
  "ComputeReceipt.v1":["compute_id","status","timestamp"],
  "ProofReceipt.v1":["proof_hash","entry_hash","verified"],
  "ReturnBlock.v3":["version","run_id","timestamp","status","decision","execution","result","violations","kdr_hash"],
  "AdapterContract.v1":["op","side_effect_class","deterministic","requires_kdr"]
 }
 @staticmethod
 def validate(packet_type:str,packet:Dict[str,Any])->tuple:
  required=ABIValidator.REQUIRED_FIELDS.get(packet_type,[])
  missing=[f for f in required if f not in packet]
  if missing:return False,f"missing fields: {missing}"
  if packet_type=="ReturnBlock.v3":
   if packet.get('decision',{}).get('allowed')is None:return False,"decision.allowed cannot be None"
   if packet.get('execution',{}).get('all_ok')is None:return False,"execution.all_ok cannot be None"
   if packet.get('result',{}).get('output_ok')is None:return False,"result.output_ok cannot be None"
   if not isinstance(packet.get('violations'),[]):return False,"violations must be list"
  return True,"valid"
