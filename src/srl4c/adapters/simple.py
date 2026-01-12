"""Simple POST adapter for basic chat endpoints"""

import time

import httpx

from srl4c.adapters.base import BaseAdapter


class SimpleAdapter(BaseAdapter):
    """Adapter for simple POST /chat style endpoints"""

    def __init__(self, base_url: str, api_key_env: str | None = None, config: dict = None):
        super().__init__(base_url, api_key_env, config)
        # Field names for request/response
        self.request_field = self.config.get("request_field", "message")
        self.response_field = self.config.get("response_field", "response")

    def send_message(self, message: str) -> str:
        """Send a message and return the response"""
        api_key = self.get_api_key()
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {self.request_field: message}

        response = httpx.post(
            self.base_url,
            json=payload,
            headers=headers,
            timeout=60.0,
        )
        response.raise_for_status()

        data = response.json()
        return data.get(self.response_field, str(data))

    def test_connection(self) -> tuple[bool, str, int | None]:
        """Test connection with a simple message"""
        try:
            start = time.time()
            response = self.send_message("Hello, this is a test.")
            latency = int((time.time() - start) * 1000)
            return True, response[:100], latency
        except httpx.HTTPStatusError as e:
            return (
                False,
                f"HTTP {e.response.status_code}: {e.response.text[:100]}",
                None,
            )
        except Exception as e:
            return False, str(e), None
