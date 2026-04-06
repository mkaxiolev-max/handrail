"""Privacy policy — secret stripping, veil gate."""
import re

SECRET_PATTERNS = [
    re.compile(r"sk_[a-zA-Z0-9_]+"),
    re.compile(r"whsec_[a-zA-Z0-9_]+"),
    re.compile(r"sk-ant-api[0-9a-zA-Z_-]+"),
    re.compile(r"AC[0-9a-f]{32}"),
]


def strip_secrets(text: str) -> str:
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


def veil(data: dict) -> dict:
    """Recursively strip secrets from a dict before sending to local models."""
    result = {}
    for k, v in data.items():
        if isinstance(v, str):
            result[k] = strip_secrets(v)
        elif isinstance(v, dict):
            result[k] = veil(v)
        else:
            result[k] = v
    return result
