"""
SRL4C OpenAI Wrapper

Wraps an OpenAI client to route calls through a guardrail proxy worker.

Usage:
    from srl4c import srl4c
    from openai import OpenAI

    client = srl4c(OpenAI(api_key="sk-...", base_url="https://api.openai.com/v1"))

    # Use normally - calls are intercepted and routed through guardrail proxy
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}]
    )
"""

import os
from pathlib import Path
from typing import Any, Optional
import httpx


def _get_worker_url() -> Optional[str]:
    """Get worker URL from env var or config file."""
    # Try env var first
    url = os.environ.get("SRL4C_WORKER_URL")
    if url:
        return url

    # Try config file
    config_path = Path.home() / ".srl4c" / "config.yaml"
    if config_path.exists():
        try:
            import yaml
            with open(config_path) as f:
                config = yaml.safe_load(f)
                if config:
                    return config.get("worker_url")
        except Exception:
            pass

    return None


def _to_obj(data):
    """Convert dict/list to object with attribute access, keep scalars as-is."""
    if isinstance(data, dict):
        return _DictToObject(data)
    elif isinstance(data, list):
        return [_to_obj(item) for item in data]
    else:
        # Keep scalars (str, int, float, None, bool) as-is
        return data


class _DictToObject:
    """Convert dict to object with attribute access (like OpenAI response)."""

    def __init__(self, data: dict):
        for key, value in data.items():
            setattr(self, key, _to_obj(value))

    def __repr__(self):
        return str({k: v for k, v in self.__dict__.items() if not k.startswith('_')})

    def __iter__(self):
        raise TypeError("Not iterable")

    def __getitem__(self, key):
        return getattr(self, key)


class GuardedChatCompletions:
    """Proxied chat.completions that routes through guardrail worker."""

    def __init__(self, original_client: Any, worker_url: str):
        self._original = original_client
        self._worker_url = worker_url.rstrip("/")

        # Extract base_url and api_key from original client
        base_url = getattr(original_client, "base_url", None)
        if base_url:
            self._target_url = str(base_url).rstrip("/")
        else:
            self._target_url = "https://api.openai.com/v1"

        self._api_key = getattr(original_client, "api_key", None)

    def create(self, **kwargs) -> Any:
        """Intercept create() and route through worker."""
        # Build payload with target info
        payload = {
            "_target": self._target_url,
            "_api_key": self._api_key,
            **kwargs
        }

        # Send to worker
        response = httpx.post(
            f"{self._worker_url}/v1/chat/completions",
            json=payload,
            timeout=120.0,
        )

        if response.status_code != 200:
            raise Exception(f"Worker error: {response.status_code} - {response.text}")

        # Return as object with same structure as OpenAI response
        return _to_obj(response.json())


class GuardedChat:
    """Proxied chat namespace."""

    def __init__(self, original_client: Any, worker_url: str):
        self.completions = GuardedChatCompletions(original_client, worker_url)


class GuardedClient:
    """Wrapper around OpenAI client that routes through guardrail worker."""

    def __init__(self, original_client: Any, worker_url: str):
        self._original = original_client
        self._worker_url = worker_url
        self.chat = GuardedChat(original_client, worker_url)

    def __getattr__(self, name: str) -> Any:
        """Pass through other attributes to original client."""
        return getattr(self._original, name)


def srl4c(client: Any, worker: Optional[str] = None) -> GuardedClient:
    """
    Wrap an OpenAI client to route calls through guardrail proxy.

    Args:
        client: An OpenAI client instance
        worker: Worker URL (optional, reads from SRL4C_WORKER_URL env or config)

    Returns:
        Wrapped client that routes through guardrail worker

    Example:
        from srl4c import srl4c
        from openai import OpenAI

        client = srl4c(OpenAI(api_key="sk-...", base_url="..."))
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello"}]
        )
    """
    worker_url = worker or _get_worker_url()

    if not worker_url:
        raise ValueError(
            "No worker URL configured. Either:\n"
            "  1. Set SRL4C_WORKER_URL environment variable\n"
            "  2. Pass worker='https://...' to srl4c()\n"
            "  3. Run 'srl4c guardrails deploy' to deploy and configure"
        )

    return GuardedClient(client, worker_url)
