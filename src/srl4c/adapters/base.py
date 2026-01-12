"""Base adapter protocol"""

import os
from abc import ABC, abstractmethod


class BaseAdapter(ABC):
    """Base class for endpoint adapters"""

    def __init__(self, base_url: str, api_key_env: str | None = None, config: dict = None):
        self.base_url = base_url.rstrip("/")
        self.api_key_env = api_key_env
        self.config = config or {}

    def get_api_key(self) -> str | None:
        """Get API key from environment variable"""
        if self.api_key_env:
            return os.environ.get(self.api_key_env)
        return None

    @abstractmethod
    def send_message(self, message: str) -> str:
        """Send a message and return the response"""
        pass

    @abstractmethod
    def test_connection(self) -> tuple[bool, str, int | None]:
        """
        Test connection to the endpoint.
        Returns: (success, response_or_error, latency_ms)
        """
        pass
