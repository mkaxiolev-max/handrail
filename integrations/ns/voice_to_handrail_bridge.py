"""NS voice intent → Handrail CPS execution."""
import requests, json
class VoiceToHandrailBridge:
    def __init__(self):
        self.ns_url = 'http://127.0.0.1:9000'
        self.handrail_url = 'http://127.0.0.1:8011/ops/cps'
    def execute_voice_intent(self, transcription):
        try:
            classify_resp = requests.post(f'{self.ns_url}/classify', json={'transcription': transcription}, timeout=3)
            intent_data = classify_resp.json()
            intent = intent_data.get('intent', 'unknown')
            cps_packet = self._build_cps(intent, transcription)
            exec_resp = requests.post(self.handrail_url, json=cps_packet, timeout=5)
            result = exec_resp.json()
            return {'intent': intent, 'cps_ok': result.get('ok'), 'receipt': result.get('results', [])}
        except Exception as e:
            return {'error': str(e), 'intent': 'unknown'}
    def _build_cps(self, intent, transcription):
        action_map = {
            'list_windows': 'list_windows',
            'capture_screen': 'capture_screen',
            'health_probe': 'health_probe',
            'open_app': 'open_app',
            'proc_run': 'proc_run',
        }
        action = action_map.get(intent, 'health_probe')
        return {
            'cps_id': f'voice_{intent}',
            'ops': [{'op': action, 'args': {}}],
        }
