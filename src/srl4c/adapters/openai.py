"""OpenAI-compatible API adapter"""

import time
from typing import Optional

import httpx

from srl4c.adapters.base import BaseAdapter


class OpenAIAdapter(BaseAdapter):
    """Adapter for OpenAI-compatible /v1/chat/completions endpoints"""

    def send_message(self, message: str) -> str:
        """Send a message and return the response"""
        api_key = self.get_api_key()
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "messages": [{"role": "user", "content": message}],
            "temperature": self.config.get("temperature", 0.7),
        }

        # Add model if specified in config
        if "model" in self.config:
            payload["model"] = self.config["model"]

        response = httpx.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=60.0,
        )
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"]

    def test_connection(self) -> tuple[bool, str, Optional[int]]:
        """Test connection with a simple message"""
        try:
            start = time.time()
            response = self.send_message("Hello, this is a test.")
            latency = int((time.time() - start) * 1000)
            return True, response[:100], latency
        except httpx.HTTPStatusError as e:
            return False, f"HTTP {e.response.status_code}: {e.response.text[:100]}", None
        except Exception as e:
            return False, str(e), None
