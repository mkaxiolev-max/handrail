"""Twilio voice webhook → NS intent → Handrail execution → TwiML response."""
from fastapi import FastAPI, Request
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
import os, json, requests
app = FastAPI()
TWILIO_SID = os.getenv('TWILIO_ACCOUNT_SID', 'AC_TEST')
TWILIO_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', 'token_test')
HANDRAIL_URL = 'http://127.0.0.1:8011/ops/cps'
NS_URL = 'http://127.0.0.1:9000'
@app.post('/twilio/voice')
async def handle_voice(request: Request):
    form = await request.form()
    caller = form.get('Caller', '+1unknown')
    transcription = form.get('SpeechResult', 'no speech')
    try:
        intent_resp = requests.post(f'{NS_URL}/classify', json={'transcription': transcription}, timeout=3)
        intent = intent_resp.json().get('intent', 'unknown')
        cps_payload = {
            'cps_id': f'voice_{intent}',
            'ops': [{'op': 'health_probe', 'args': {'service': 'handrail'}}],
        }
        exec_resp = requests.post(HANDRAIL_URL, json=cps_payload, timeout=5)
        ok = exec_resp.json().get('ok', False)
        response = VoiceResponse()
        if ok:
            response.say(f'Intent {intent} executed successfully')
        else:
            response.say('System error. Please try again.')
        response.hangup()
        return str(response)
    except Exception as e:
        response = VoiceResponse()
        response.say(f'Error: {str(e)[:50]}')
        response.hangup()
        return str(response)
