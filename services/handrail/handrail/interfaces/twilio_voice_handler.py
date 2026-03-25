"""Twilio inbound → NS classifier → Handrail CPS → TwiML response"""
from fastapi import FastAPI, Request
from twilio.twiml.voice_response import VoiceResponse
import requests, os, json
app = FastAPI()
INTENT_MAP = {
    'list': 'list_files', 'capture': 'capture_screen', 'check': 'health_probe',
    'status': 'proc_run', 'open': 'open_app', 'run': 'proc_run',
}
@app.post('/twilio/voice')
async def handle_voice(request: Request):
    form = await request.form()
    caller = form.get('Caller', '+1unknown')
    text = form.get('SpeechResult', '').lower()
    try:
        intent = next((act for kw, act in INTENT_MAP.items() if kw in text), 'health_probe')
        cps = {'cps_id': f'voice_{intent}', 'ops': [{'op': intent, 'args': {}}]}
        resp = requests.post('http://127.0.0.1:8011/ops/cps', json=cps, timeout=5)
        ok = resp.json().get('ok', False)
        twiml = VoiceResponse()
        twiml.say('Executed' if ok else 'Error')
        twiml.hangup()
        return str(twiml)
    except Exception as e:
        twiml = VoiceResponse()
        twiml.say('System error')
        twiml.hangup()
        return str(twiml)
