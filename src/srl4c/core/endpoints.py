"""Endpoint business logic."""

import time
from typing import Optional

from srl4c.db.repository import EndpointRepository
from srl4c.adapters.openai import OpenAIAdapter
from srl4c.adapters.simple import SimpleAdapter


def _get_adapter(endpoint):
    """Create the appropriate adapter for an endpoint."""
    if endpoint.type == "openai":
        return OpenAIAdapter(endpoint.base_url, endpoint.api_key_env, endpoint.config)
    else:
        return SimpleAdapter(endpoint.base_url, endpoint.api_key_env, endpoint.config)


def send_prompt(endpoint_name: str, prompt: str) -> dict:
    """
    Send a prompt to an endpoint and return the response.

    Args:
        endpoint_name: Endpoint ID or name
        prompt: The prompt text to send

    Returns:
        dict with keys: success, response, latency_ms, error

    Raises:
        ValueError: If endpoint not found
    """
    endpoint = EndpointRepository.get_by_id_or_name(endpoint_name)
    if not endpoint:
        raise ValueError(f"Endpoint not found: {endpoint_name}")

    adapter = _get_adapter(endpoint)

    try:
        start = time.time()
        response = adapter.send_message(prompt)
        latency_ms = int((time.time() - start) * 1000)

        # Update last used timestamp
        EndpointRepository.update_last_used(endpoint.id)

        return {
            "success": True,
            "response": response,
            "latency_ms": latency_ms,
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "response": None,
            "latency_ms": None,
            "error": str(e),
        }


def test_endpoint(endpoint_name: str) -> dict:
    """
    Test endpoint connectivity with a default message.

    Args:
        endpoint_name: Endpoint ID or name

    Returns:
        dict with keys: success, response, latency_ms, error

    Raises:
        ValueError: If endpoint not found
    """
    return send_prompt(endpoint_name, "Hello!")
