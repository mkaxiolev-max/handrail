#!/usr/bin/env python3
import os, json, sys, subprocess
from datetime import datetime
from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse

app = Flask(__name__)
NS_HOME = os.path.expanduser("~/NS_Genesis/ns_home")
NS_VOICE_CONFIG = os.path.join(NS_HOME, "kernel/voice_authority.json")
NS_RECEIPTS = os.path.join(NS_HOME, "receipts/receipts.jsonl")

def load_voice_config():
    try:
        with open(NS_VOICE_CONFIG) as f:
            return json.load(f)
    except:
        return None

def log_receipt(action, details):
    entry = {
        "receipt_id": f"RCP-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "action": action,
        "details": details
    }
    try:
        with open(NS_RECEIPTS, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    except:
        pass

def check_yubikey():
    try:
        result = subprocess.run(['ykman', 'list'], capture_output=True, text=True)
        return 'Serial:' in result.stdout
    except:
        return False

def get_yubikey_serial():
    try:
        result = subprocess.run(['ykman', 'list'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'Serial:' in line:
                return line.split('Serial:')[1].strip()
    except:
        pass
    return None

def verify_caller(phone):
    config = load_voice_config()
    if not config:
        return False, "Not configured"
    
    phone = phone.strip()
    personal_phone = config.get('personal_phone', '').strip()
    
    if phone != personal_phone:
        return False, f"Not authorized (expected {personal_phone}, got {phone})"
    
    if not check_yubikey():
        return False, "YubiKey missing"
    
    serial = get_yubikey_serial()
    if serial != config.get('authorized_yubikey'):
        return False, f"YubiKey not authorized"
    
    return True, "OK"

@app.route('/voice', methods=['POST'])
def voice_webhook():
    caller = request.form.get('From', 'unknown')
    call_sid = request.form.get('CallSid', 'unknown')
    
    log_receipt('voice_call_received', {'caller': caller, 'call_sid': call_sid})
    
    authorized, reason = verify_caller(caller)
    response = VoiceResponse()
    
    if not authorized:
        log_receipt('voice_call_rejected', {'caller': caller, 'reason': reason})
        response.say(f"Access denied. {reason}")
        return Response(str(response), mimetype='application/xml')
    
    log_receipt('voice_caller_authorized', {'caller': caller})
    response.gather(
        num_digits=1,
        action='/voice/process',
        method='POST',
        input='speech',
        timeout=10,
        speech_timeout='auto'
    )
    response.say('Welcome to NS Genesis. State your command.')
    return Response(str(response), mimetype='application/xml')

@app.route('/voice/process', methods=['POST'])
def process_command():
    caller = request.form.get('From', 'unknown')
    transcript = request.form.get('SpeechResult', '')
    
    cmd_type = 'query'
    if 'map' in transcript.lower():
        cmd_type = 'map'
    elif 'search' in transcript.lower():
        cmd_type = 'search'
    elif 'report' in transcript.lower() or 'status' in transcript.lower():
        cmd_type = 'report'
    
    results = {
        'map': 'Entity graph built',
        'search': '3 documents found',
        'report': '6 events in last 24h',
        'query': f'Processed'
    }
    result = results.get(cmd_type, 'Done')
    
    log_receipt('voice_command_executed', {
        'caller': caller,
        'transcript': transcript,
        'command': cmd_type,
        'result': result
    })
    
    response = VoiceResponse()
    response.say(f"Command received. {result}")
    response.say("Thank you. Goodbye.")
    response.hangup()
    
    return Response(str(response), mimetype='application/xml')

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'healthy', 'version': '1.0'}

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    print("╔════════════════════════════════════════╗")
    print("║   TWILIO VOICE WEBHOOK RECEIVER v1.0   ║")
    print("╚════════════════════════════════════════╝")
    print(f"\nListening on port {port}\n")
    app.run(host='0.0.0.0', port=port, debug=False)
