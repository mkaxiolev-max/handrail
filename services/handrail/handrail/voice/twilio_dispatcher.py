import json
from typing import Dict, Any, Tuple
from datetime import datetime
class TwilioVoiceHandler:
 def __init__(self):self.call_log=[]
 def parse_inbound_sms(self,from_number:str,message_body:str)->Dict[str,Any]:return{"from":from_number,"body":message_body,"timestamp":datetime.utcnow().isoformat()+"Z","type":"sms"}
 def parse_inbound_voice(self,from_number:str,speech_text:str)->Dict[str,Any]:return{"from":from_number,"speech":speech_text,"timestamp":datetime.utcnow().isoformat()+"Z","type":"voice"}
 def create_intent_from_input(self,inbound:Dict[str,Any])->Dict[str,Any]:m=inbound.get('body')or inbound.get('speech','');return{"intent_id":f"voice_{datetime.utcnow().timestamp()}","input_type":inbound.get('type'),"from":inbound.get('from'),"message":m,"timestamp":inbound.get('timestamp')}
 def dispatch_to_kdr(self,intent:Dict[str,Any],kdr_handler)->Dict[str,Any]:return kdr_handler.dispatch_with_receipt(intent)
 def execute_intent(self,kdr_result:Dict[str,Any],executor)->Dict[str,Any]:
  if kdr_result.get('allowed')!=True:return{"status":"REJECTED","reason":"KDR decision denied"}
  return executor.execute(kdr_result)
 def generate_voice_response(self,rb:Dict[str,Any])->str:
  if rb.get('status')!="SUCCESS":return "Operation failed. Please try again."
  summary=rb.get('result',{}).get('summary','Operation completed')
  return f"Success. {summary}. Message recorded in system ledger."
 def generate_twilio_response(self,response_text:str,inbound_type:str)->str:
  if inbound_type=="sms":return response_text
  twiml=f'<?xml version="1.0" encoding="UTF-8"?><Response><Say>{response_text}</Say></Response>'
  return twiml
 def full_pipeline(self,from_number:str,input_text:str,input_type:str,kdr_handler,executor)->Tuple[str,Dict[str,Any]]:
  inbound=self.parse_inbound_sms(from_number,input_text)if input_type=="sms"else self.parse_inbound_voice(from_number,input_text)
  intent=self.create_intent_from_input(inbound)
  kdr_result=self.dispatch_to_kdr(intent,kdr_handler)
  rb=self.execute_intent(kdr_result,executor)
  response_text=self.generate_voice_response(rb)
  twilio_response=self.generate_twilio_response(response_text,input_type)
  self.call_log.append({"from":from_number,"input_type":input_type,"status":rb.get('status'),"timestamp":datetime.utcnow().isoformat()+"Z"})
  return twilio_response,rb
