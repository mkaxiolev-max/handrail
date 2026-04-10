"""
NS∞ Model Router v2.1 — multi-provider LLM adjudication.
AXIOLEV Holdings LLC · Copyright © 2024-2026 · Wyoming, USA

Supports: Anthropic Claude, OpenAI GPT, Google Gemini, xAI Grok, Groq, Ollama (local).
Falls back gracefully when a provider key is absent.
Primary engine: claude-haiku-4-5-20251001 (always active when credits present).
Ollama: always attempted — no key needed, reaches host.docker.internal:11434.
"""
from __future__ import annotations
import os
import time
import logging
import asyncio
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("model_router")

app = FastAPI(title="NS∞ Model Router", version="2.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Provider key detection ─────────────────────────────────────────────────
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_KEY    = os.environ.get("OPENAI_API_KEY", "")
GEMINI_KEY    = os.environ.get("GOOGLE_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")
GROK_KEY      = os.environ.get("XAI_API_KEY", "")
GROQ_KEY      = os.environ.get("GROQ_API_KEY", "")
OLLAMA_HOST   = os.environ.get("OLLAMA_HOST", "host.docker.internal")
OLLAMA_PORT   = os.environ.get("OLLAMA_PORT", "11434")
OLLAMA_MODEL  = os.environ.get("OLLAMA_DEFAULT_MODEL", "llama3:latest")
OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"

def key_live(k: str) -> bool:
    return bool(k) and k not in ("", "PENDING", "sk-pending", "YOUR_KEY_HERE") and len(k) > 10

PROVIDERS: dict[str, dict] = {
    "anthropic": {
        "live": key_live(ANTHROPIC_KEY),
        "key_env": "ANTHROPIC_API_KEY",
        "primary_model": "claude-haiku-4-5-20251001",
        "always_active": True,
        "local": False,
    },
    "openai": {
        "live": key_live(OPENAI_KEY),
        "key_env": "OPENAI_API_KEY",
        "primary_model": "gpt-4o-mini",
        "always_active": False,
        "local": False,
    },
    "gemini": {
        "live": key_live(GEMINI_KEY),
        "key_env": "GOOGLE_API_KEY",
        "primary_model": "gemini-1.5-flash",
        "always_active": False,
        "local": False,
    },
    "grok": {
        "live": key_live(GROK_KEY),
        "key_env": "XAI_API_KEY",
        "primary_model": "grok-beta",
        "always_active": False,
        "local": False,
    },
    "groq": {
        "live": key_live(GROQ_KEY),
        "key_env": "GROQ_API_KEY",
        "primary_model": "llama-3.3-70b-versatile",
        "always_active": False,
        "local": False,
    },
    "ollama": {
        "live": True,  # availability checked at runtime — no key needed
        "key_env": "OLLAMA_HOST",
        "primary_model": OLLAMA_MODEL,
        "always_active": True,
        "local": True,
    },
}

for name, cfg in PROVIDERS.items():
    status = "LIVE" if cfg["live"] else ("ALWAYS_ON" if cfg["always_active"] else "DEFERRED")
    local_tag = " [LOCAL]" if cfg.get("local") else ""
    logger.info(f"  {name:12s}: {status}  model={cfg['primary_model']}{local_tag}")

# ── Anthropic ──────────────────────────────────────────────────────────────
async def call_anthropic(prompt: str, model: str = "claude-haiku-4-5-20251001",
                          system: str = "", max_tokens: int = 1024) -> dict:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY or None)
        msgs = [{"role": "user", "content": prompt}]
        kwargs: dict = {"model": model, "max_tokens": max_tokens, "messages": msgs}
        if system:
            kwargs["system"] = system
        resp = client.messages.create(**kwargs)
        text = resp.content[0].text if resp.content else ""
        return {
            "provider": "anthropic", "model": model, "text": text, "ok": True,
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
        }
    except ImportError:
        return {"provider": "anthropic", "model": model, "ok": False, "error": "anthropic package not installed"}
    except Exception as e:
        return {"provider": "anthropic", "model": model, "ok": False, "error": str(e)}

# ── OpenAI ─────────────────────────────────────────────────────────────────
async def call_openai(prompt: str, model: str = "gpt-4o-mini",
                       system: str = "", max_tokens: int = 1024) -> dict:
    if not key_live(OPENAI_KEY):
        return {"provider": "openai", "model": model, "ok": False, "error": "OPENAI_API_KEY not configured"}
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=OPENAI_KEY)
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        resp = await client.chat.completions.create(model=model, messages=msgs, max_tokens=max_tokens)
        text = resp.choices[0].message.content or ""
        return {
            "provider": "openai", "model": model, "text": text, "ok": True,
            "input_tokens": resp.usage.prompt_tokens,
            "output_tokens": resp.usage.completion_tokens,
        }
    except ImportError:
        return {"provider": "openai", "model": model, "ok": False, "error": "openai package not installed"}
    except Exception as e:
        return {"provider": "openai", "model": model, "ok": False, "error": str(e)}

# ── Gemini ─────────────────────────────────────────────────────────────────
async def call_gemini(prompt: str, model: str = "gemini-1.5-flash",
                       system: str = "", max_tokens: int = 1024) -> dict:
    if not key_live(GEMINI_KEY):
        return {"provider": "gemini", "model": model, "ok": False, "error": "GOOGLE_API_KEY not configured"}
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_KEY)
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        m = genai.GenerativeModel(model)
        resp = m.generate_content(full_prompt)
        text = resp.text or ""
        return {
            "provider": "gemini", "model": model, "text": text, "ok": True,
            "input_tokens": getattr(resp.usage_metadata, "prompt_token_count", 0),
            "output_tokens": getattr(resp.usage_metadata, "candidates_token_count", 0),
        }
    except ImportError:
        return {"provider": "gemini", "model": model, "ok": False, "error": "google-generativeai not installed"}
    except Exception as e:
        return {"provider": "gemini", "model": model, "ok": False, "error": str(e)}

# ── xAI Grok ──────────────────────────────────────────────────────────────
async def call_grok(prompt: str, model: str = "grok-beta",
                     system: str = "", max_tokens: int = 1024) -> dict:
    if not key_live(GROK_KEY):
        return {"provider": "grok", "model": model, "ok": False, "error": "XAI_API_KEY not configured"}
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=GROK_KEY, base_url="https://api.x.ai/v1")
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        resp = await client.chat.completions.create(model=model, messages=msgs, max_tokens=max_tokens)
        text = resp.choices[0].message.content or ""
        return {
            "provider": "grok", "model": model, "text": text, "ok": True,
            "input_tokens": resp.usage.prompt_tokens,
            "output_tokens": resp.usage.completion_tokens,
        }
    except ImportError:
        return {"provider": "grok", "model": model, "ok": False, "error": "openai package not installed"}
    except Exception as e:
        return {"provider": "grok", "model": model, "ok": False, "error": str(e)}

# ── Groq ───────────────────────────────────────────────────────────────────
async def call_groq(prompt: str, model: str = "llama-3.3-70b-versatile",
                     system: str = "", max_tokens: int = 1024) -> dict:
    if not key_live(GROQ_KEY):
        return {"provider": "groq", "model": model, "ok": False, "error": "GROQ_API_KEY not configured"}
    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=GROQ_KEY)
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        resp = await client.chat.completions.create(model=model, messages=msgs, max_tokens=max_tokens)
        text = resp.choices[0].message.content or ""
        return {
            "provider": "groq", "model": model, "text": text, "ok": True,
            "input_tokens": resp.usage.prompt_tokens,
            "output_tokens": resp.usage.completion_tokens,
        }
    except ImportError:
        return {"provider": "groq", "model": model, "ok": False, "error": "groq package not installed"}
    except Exception as e:
        return {"provider": "groq", "model": model, "ok": False, "error": str(e)}

# ── Ollama (local) ─────────────────────────────────────────────────────────
async def call_ollama(prompt: str, model: str = None,
                       system: str = "", max_tokens: int = 1024) -> dict:
    """
    Calls local Ollama via its OpenAI-compatible API.
    Ollama runs on the host Mac at host.docker.internal:11434.
    No API key needed. Falls back gracefully if not reachable.
    """
    actual_model = model or OLLAMA_MODEL
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key="ollama",  # required by openai lib, ignored by ollama
            base_url=f"{OLLAMA_BASE_URL}/v1",
        )
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        resp = await client.chat.completions.create(
            model=actual_model,
            messages=msgs,
            max_tokens=max_tokens,
        )
        text = resp.choices[0].message.content or ""
        return {
            "provider": "ollama",
            "model": actual_model,
            "text": text,
            "ok": True,
            "local": True,
            "input_tokens": getattr(resp.usage, "prompt_tokens", 0),
            "output_tokens": getattr(resp.usage, "completion_tokens", 0),
        }
    except ImportError:
        return {"provider": "ollama", "model": actual_model, "ok": False,
                "error": "openai package not installed (needed for ollama compat)"}
    except Exception as e:
        err = str(e)
        if "Connection" in err or "connect" in err.lower():
            return {"provider": "ollama", "model": actual_model, "ok": False,
                    "error": f"Ollama not reachable at {OLLAMA_BASE_URL} — is it running on the host?"}
        return {"provider": "ollama", "model": actual_model, "ok": False, "error": err}

PROVIDER_FN = {
    "anthropic": call_anthropic,
    "openai":    call_openai,
    "gemini":    call_gemini,
    "grok":      call_grok,
    "groq":      call_groq,
    "ollama":    call_ollama,
}

# ── Request models ─────────────────────────────────────────────────────────
class CompletionRequest(BaseModel):
    prompt: str
    provider: str = "anthropic"
    model: Optional[str] = None
    system: str = ""
    max_tokens: int = 1024

class AdjudicationRequest(BaseModel):
    prompt: str
    providers: list[str] = ["anthropic"]
    system: str = ""
    max_tokens: int = 1024

# ── Routes ─────────────────────────────────────────────────────────────────
@app.get("/healthz")
async def healthz():
    live = [n for n, c in PROVIDERS.items() if c["live"] or c["always_active"]]
    return {
        "status": "ok",
        "service": "model_router",
        "version": "2.1.0",
        "active_providers": live,
        "primary": "anthropic",
        "primary_model": "claude-haiku-4-5-20251001",
        "local_llm": OLLAMA_MODEL,
        "providers": {
            name: {
                "live": cfg["live"],
                "always_active": cfg["always_active"],
                "model": cfg["primary_model"],
                "key_present": key_live(os.environ.get(cfg["key_env"], "")),
                "local": cfg.get("local", False),
            }
            for name, cfg in PROVIDERS.items()
        },
    }

@app.get("/providers")
async def providers():
    return {
        "providers": {
            name: {
                "live": cfg["live"],
                "always_active": cfg["always_active"],
                "primary_model": cfg["primary_model"],
                "key_env": cfg["key_env"],
                "key_present": key_live(os.environ.get(cfg["key_env"], "")),
                "local": cfg.get("local", False),
            }
            for name, cfg in PROVIDERS.items()
        }
    }

@app.get("/ollama/models")
async def ollama_models():
    """List models available in the local Ollama instance."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            data = resp.json()
            models = data.get("models", [])
            return {
                "ollama_url": OLLAMA_BASE_URL,
                "model_count": len(models),
                "default_model": OLLAMA_MODEL,
                "models": [
                    {
                        "name": m.get("name"),
                        "size_gb": round(m.get("size", 0) / 1e9, 1),
                        "modified": m.get("modified_at", "")[:10],
                    }
                    for m in models
                ],
            }
    except Exception as e:
        return {
            "ollama_url": OLLAMA_BASE_URL,
            "error": str(e),
            "hint": "Ollama may not be running — start with: ollama serve",
        }

@app.post("/complete")
async def complete(req: CompletionRequest):
    provider = req.provider.lower()
    if provider not in PROVIDER_FN:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    fn = PROVIDER_FN[provider]
    model = req.model or PROVIDERS[provider]["primary_model"]
    t0 = time.time()
    result = await fn(req.prompt, model=model, system=req.system, max_tokens=req.max_tokens)
    result["latency_ms"] = round((time.time() - t0) * 1000, 1)
    return result

@app.post("/adjudicate")
async def adjudicate(req: AdjudicationRequest):
    """Run prompt across multiple providers and return all responses."""
    providers_to_run = [p for p in req.providers if p in PROVIDER_FN] or ["anthropic"]

    async def run_one(p: str) -> dict:
        fn = PROVIDER_FN[p]
        model = PROVIDERS[p]["primary_model"]
        t0 = time.time()
        r = await fn(req.prompt, model=model, system=req.system, max_tokens=req.max_tokens)
        r["latency_ms"] = round((time.time() - t0) * 1000, 1)
        return r

    results = await asyncio.gather(*[run_one(p) for p in providers_to_run])
    successful = [r for r in results if r.get("ok")]
    return {
        "results": list(results),
        "successful_count": len(successful),
        "failed_count": len(results) - len(successful),
        "providers_ran": providers_to_run,
    }

@app.post("/probe")
async def probe_all():
    """Probe all providers with a minimal test prompt."""
    test_prompt = "Reply with exactly: NS online"

    async def probe_one(name: str) -> dict:
        fn = PROVIDER_FN[name]
        model = PROVIDERS[name]["primary_model"]
        t0 = time.time()
        r = await fn(test_prompt, model=model, max_tokens=20)
        r["latency_ms"] = round((time.time() - t0) * 1000, 1)
        r["provider_name"] = name
        return r

    results = await asyncio.gather(*[probe_one(p) for p in PROVIDER_FN])
    return {
        "probe_results": {r["provider_name"]: {
            "ok": r.get("ok"),
            "latency_ms": r.get("latency_ms"),
            "text_preview": r.get("text", "")[:60],
            "error": r.get("error"),
            "local": r.get("local", False),
        } for r in results}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9002)
