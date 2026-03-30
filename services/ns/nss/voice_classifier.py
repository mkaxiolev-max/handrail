"""Intent classifier for voice transcriptions."""
import json
intent_map = {
    'list': 'list_windows',
    'capture': 'capture_screen',
    'open': 'open_app',
    'check': 'health_probe',
    'run': 'proc_run',
    'status': 'health_probe',
}
def classify(transcription):
    for keyword, intent in intent_map.items():
        if keyword in transcription.lower():
            return {'intent': intent, 'confidence': 0.9, 'transcription': transcription}
    return {'intent': 'unknown', 'confidence': 0.0, 'transcription': transcription}
