"""Minimal CPS Action Grammar — 12 core actions only."""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class Action:
    action: str
    args: Dict[str, Any]
    permissions_required: List[str]

CORE_ACTIONS = {
    'list_windows': {'args_schema': {}, 'permissions': ['ui.read']},
    'get_focused_window': {'args_schema': {}, 'permissions': ['ui.read']},
    'capture_screen': {'args_schema': {'output_path': str}, 'permissions': ['ui.read', 'file.write']},
    'capture_window': {'args_schema': {'window_id': str, 'output_path': str}, 'permissions': ['ui.read', 'file.write']},
    'focus_window': {'args_schema': {'window_id': str}, 'permissions': ['ui.write']},
    'open_app': {'args_schema': {'app_name': str}, 'permissions': ['ui.write']},
    'open_url': {'args_schema': {'url': str}, 'permissions': ['ui.write']},
    'type_text': {'args_schema': {'text': str}, 'permissions': ['ui.write']},
    'keypress': {'args_schema': {'key': str, 'modifiers': list}, 'permissions': ['ui.write']},
    'http_get': {'args_schema': {'url': str}, 'permissions': ['network.read']},
    'proc_run': {'args_schema': {'cmd': str}, 'permissions': ['process.exec']},
    'health_probe': {'args_schema': {'service': str}, 'permissions': ['network.read']},
}

def validate_action(action_name: str, args: Dict) -> bool:
    if action_name not in CORE_ACTIONS:
        return False
    schema = CORE_ACTIONS[action_name]['args_schema']
    return all(k in args for k in schema.keys())

def get_permissions(action_name: str) -> List[str]:
    return CORE_ACTIONS.get(action_name, {}).get('permissions', [])
