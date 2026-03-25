"""Mac Adapter Capability Registry — declares all available actions."""
import json
from typing import Dict, List
class CapabilityRegistry:
    def __init__(self):
        self.capabilities = {
            'ui.read': ['list_windows', 'get_focused_window', 'capture_screen', 'capture_window'],
            'ui.write': ['focus_window', 'open_app', 'open_url', 'type_text', 'keypress'],
            'file.write': ['capture_screen', 'capture_window'],
            'network.read': ['http_get', 'health_probe'],
            'process.exec': ['proc_run'],
        }
        self.action_metadata = {
            'list_windows': {'description': 'List all open windows', 'result_type': 'list'},
            'get_focused_window': {'description': 'Get currently focused window', 'result_type': 'object'},
            'capture_screen': {'description': 'Capture full screen to file', 'result_type': 'file'},
            'capture_window': {'description': 'Capture single window to file', 'result_type': 'file'},
            'focus_window': {'description': 'Bring window to focus', 'result_type': 'boolean'},
            'open_app': {'description': 'Launch application by name', 'result_type': 'boolean'},
            'open_url': {'description': 'Open URL in default browser', 'result_type': 'boolean'},
            'type_text': {'description': 'Type text via keyboard', 'result_type': 'boolean'},
            'keypress': {'description': 'Send keypress with modifiers', 'result_type': 'boolean'},
            'http_get': {'description': 'HTTP GET request', 'result_type': 'object'},
            'proc_run': {'description': 'Run shell command', 'result_type': 'object'},
            'health_probe': {'description': 'Check service health', 'result_type': 'boolean'},
        }
    def list_actions(self) -> List[str]:
        return list(self.action_metadata.keys())
    def get_action_metadata(self, action: str) -> Dict:
        return self.action_metadata.get(action, {})
    def check_permission(self, action: str, permission: str) -> bool:
        for perm, actions in self.capabilities.items():
            if perm == permission and action in actions:
                return True
        return False
