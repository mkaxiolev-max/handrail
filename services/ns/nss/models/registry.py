# Copyright © 2026 Axiolev. All rights reserved.
"""
Model Registry — 5 models across providers.
Enabled status driven by env vars at runtime.
"""
import os

MODEL_REGISTRY: dict = {
    "guardian": {
        "model_key":     "guardian",
        "provider":      "local_ollama",
        "endpoint":      "http://localhost:11434/api/generate",
        "model_id":      "llama3.2",
        "role":          "guardian",
        "privacy_class": "full",       # stays fully local
        "graceful_skip": True,
        "_enable_env":   None,         # always enabled if Ollama is running
    },
    "analyst": {
        "model_key":     "analyst",
        "provider":      "anthropic",
        "model_id":      "claude-sonnet-4-6",
        "role":          "analyst",
        "privacy_class": "private_cloud",
        "graceful_skip": False,
        "_enable_env":   "ANTHROPIC_API_KEY",
    },
    "forge": {
        "model_key":     "forge",
        "provider":      "xai",
        "model_id":      "grok-2",
        "role":          "forge",
        "privacy_class": "private_cloud",
        "graceful_skip": True,
        "_enable_env":   "XAI_API_KEY",
    },
    "critic": {
        "model_key":     "critic",
        "provider":      "deepseek",
        "model_id":      "deepseek-reasoner",
        "role":          "critic",
        "privacy_class": "private_cloud",
        "graceful_skip": True,
        "_enable_env":   "DEEPSEEK_API_KEY",
    },
    "generalist": {
        "model_key":     "generalist",
        "provider":      "openai",
        "model_id":      "gpt-4o",
        "role":          "generalist",
        "privacy_class": "private_cloud",
        "graceful_skip": True,
        "_enable_env":   "OPENAI_API_KEY",
    },
}


def get_registry_with_status() -> list[dict]:
    """Return registry entries with live enabled status."""
    result = []
    for key, m in MODEL_REGISTRY.items():
        env_key = m.get("_enable_env")
        if env_key is None:
            # guardian: enabled if env var OLLAMA_ENABLED is not "false"
            enabled = os.environ.get("OLLAMA_ENABLED", "true").lower() != "false"
        else:
            enabled = bool(os.environ.get(env_key, ""))
        entry = {k: v for k, v in m.items() if not k.startswith("_")}
        entry["enabled"] = enabled
        result.append(entry)
    return result
