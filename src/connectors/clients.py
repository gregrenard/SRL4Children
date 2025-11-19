"""
Safety Readiness Level for Children - LLM-based Evaluation
Translating Design Principles into Automated guardrails and replay alignement for child safety.
Author: Gregory Renard (with GenAI: Claude, Gemini, Codex)
Organization: Everyone.AI | Year: 2025
For the well-being and safety of our children
"""

import os, subprocess, shutil, requests, json
from typing import List, Optional

def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)

def openai_generate(prompt: str, model: str = "gpt-4o-mini") -> str:
    import openai
    client = openai.OpenAI(api_key=_env("OPENAI_API_KEY"))
    resp = client.chat.completions.create(model=model, messages=[{"role":"user","content":prompt}])
    return resp.choices[0].message.content

def anthropic_generate(prompt: str, model: str = "claude-3-5-sonnet-20240620") -> str:
    import anthropic
    client = anthropic.Client(api_key=_env("ANTHROPIC_API_KEY"))
    msg = client.messages.create(model=model, max_tokens=800, messages=[{"role":"user","content":prompt}])
    return "".join([b.text for b in msg.content if getattr(b,"type",None)=="text"])

def groq_generate(prompt: str, model: str = "llama3-70b-8192") -> str:
    from groq import Groq
    client = Groq(api_key=_env("GROQ_API_KEY"))
    resp = client.chat.completions.create(model=model, messages=[{"role":"user","content":prompt}])
    return resp.choices[0].message.content

def mistral_generate(prompt: str, model: str = "mistral-large-latest") -> str:
    from mistralai import Mistral
    client = Mistral(api_key=_env("MISTRAL_API_KEY"))
    resp = client.chat.complete(model=model, messages=[{"role":"user","content":prompt}])
    return resp.choices[0].message["content"]

def ollama_models() -> List[str]:
    if shutil.which("ollama") is None:
        return []
    out = subprocess.run(["ollama","list"], capture_output=True, text=True)
    models = []
    lines = out.stdout.splitlines()
    for line in lines[1:]:
        if not line.strip():
            continue
        models.append(line.split()[0])
    return models

def ollama_generate(prompt: str, model: str, host: str = "localhost", port: int = 11434, **kwargs) -> str:
    """
    Generate a response via local or remote Ollama

    Args:
        prompt: The prompt to send
        model: The Ollama model to use
        host: Ollama host (localhost or remote IP)
        port: Ollama port (11434 by default, 11435 for SSH tunnel)
    """
    # Try via HTTP API first (more reliable for remote servers)
    try:
        # Extract specific HTTP request timeout if provided
        request_timeout = kwargs.pop("request_timeout", None) or kwargs.pop("timeout_seconds", None) or 120
        url = f"http://{host}:{port}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }

        # Add all optional Ollama parameters passed in kwargs
        # (e.g.: keep_alive, main_gpu, num_ctx, num_batch, num_thread, temperature, top_p, etc.)
        if kwargs:
            # Top-level fields supported by Ollama API
            if 'keep_alive' in kwargs and kwargs['keep_alive']:
                payload['keep_alive'] = kwargs.get('keep_alive')
            if 'format' in kwargs and kwargs['format']:
                payload['format'] = kwargs.get('format')  # e.g.: "json"
            # Recreate an options dict without keep_alive/format
            opt = {k: v for k, v in kwargs.items() if k not in ('keep_alive','format')}
            if opt:
                payload['options'] = payload.get('options', {})
                for k, v in opt.items():
                    payload['options'][k] = v

        response = requests.post(url, json=payload, timeout=request_timeout)
        response.raise_for_status()

        result = response.json()
        return result.get("response", "").strip()

    except Exception as e:
        # Fallback to local CLI if API fails and we're on localhost
        if host == "localhost" and port == 11434 and shutil.which("ollama"):
            proc = subprocess.run(["ollama","run",model], input=prompt, text=True, capture_output=True, timeout=120)
            if proc.returncode == 0:
                return proc.stdout.strip()

        raise RuntimeError(f"Ollama connection failed: {e}")

def ollama_stop(model: str, host: str = "localhost", port: int = 11434, request_timeout: int = 30) -> bool:
    """Stop an Ollama model (frees VRAM) via /api/stop.
    Returns True if the request was accepted.
    """
    import requests
    try:
        url = f"http://{host}:{port}/api/stop"
        payload = {"model": model}
        resp = requests.post(url, json=payload, timeout=request_timeout)
        if resp.status_code in (200, 204):
            return True
        # Some versions return 404 if no active runner: this is not fatal
        if resp.status_code == 404:
            return False
        resp.raise_for_status()
        return True
    except Exception:
        return False

PROVIDERS = {
    "openai": openai_generate,
    "anthropic": anthropic_generate,
    "groq": groq_generate,
    "mistral": mistral_generate,
    "ollama": ollama_generate
}
