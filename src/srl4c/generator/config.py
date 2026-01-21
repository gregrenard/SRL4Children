"""Generator configuration for guardrail generation"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from srl4c.paths import PROJECT_ROOT, TEMPLATES_DIR, USER_CONFIG_DIR

# Load API keys from .env
load_dotenv(PROJECT_ROOT / ".env")


@dataclass
class GeneratorConfig:
    """Configuration for a guardrail generator"""

    name: str
    provider_openai_base_url: str
    model: str
    api_key_env: str | None = None
    temperature: float = 0.7
    max_tokens: int = 1000
    input_cost_per_1m: float | None = None  # Cost per 1M input tokens (USD)
    output_cost_per_1m: float | None = None  # Cost per 1M output tokens (USD)

    def get_api_key(self) -> str | None:
        """Get API key from environment"""
        if self.api_key_env:
            return os.environ.get(self.api_key_env)
        return "unused"  # For local models

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float | None:
        """Calculate cost for a request. Returns None if pricing not configured."""
        if self.input_cost_per_1m is None or self.output_cost_per_1m is None:
            return None
        input_cost = (input_tokens / 1_000_000) * self.input_cost_per_1m
        output_cost = (output_tokens / 1_000_000) * self.output_cost_per_1m
        return input_cost + output_cost


def get_settings() -> dict[str, Any]:
    """Load settings from ~/.srl4c/settings.yaml"""
    settings_path = USER_CONFIG_DIR / "settings.yaml"
    if settings_path.exists():
        with open(settings_path) as f:
            return yaml.safe_load(f) or {}
    return {}


def get_active_generators_file() -> str:
    """Get the currently active generators filename"""
    return get_settings().get("active_generators", "default.generators")


def set_active_generators(filename: str) -> None:
    """Set the active generators file in settings"""
    settings = get_settings()
    settings["active_generators"] = filename
    settings_path = USER_CONFIG_DIR / "settings.yaml"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_path, "w") as f:
        yaml.dump(settings, f)


def list_generator_files() -> list[dict[str, Any]]:
    """List all available .generators files with metadata"""
    generator_files = []

    if USER_CONFIG_DIR.exists():
        for f in USER_CONFIG_DIR.glob("*.generators"):
            try:
                with open(f) as fp:
                    data = yaml.safe_load(fp) or {}
                generator_files.append(
                    {
                        "name": f.name,
                        "path": str(f),
                        "model": data.get("model", "unknown"),
                        "base_url": data.get("provider_openai_base_url", ""),
                        "is_active": f.name == get_active_generators_file(),
                    }
                )
            except Exception:
                generator_files.append(
                    {
                        "name": f.name,
                        "path": str(f),
                        "model": "error",
                        "base_url": "",
                        "is_active": f.name == get_active_generators_file(),
                        "error": "Failed to parse",
                    }
                )

    return sorted(generator_files, key=lambda x: x["name"])


def get_generator_file_content(filename: str) -> str | None:
    """Get the raw content of a generators file"""
    path = USER_CONFIG_DIR / filename
    if path.exists() and path.suffix == ".generators":
        return path.read_text()
    return None


def load_generator_config(config_path: Path = None) -> GeneratorConfig:
    """Load generator configuration from .generators file"""
    if config_path is None:
        active_file = get_active_generators_file()
        user_config = USER_CONFIG_DIR / active_file

        # Fallback chain
        if user_config.exists():
            config_path = user_config
        elif (USER_CONFIG_DIR / "default.generators").exists():
            config_path = USER_CONFIG_DIR / "default.generators"
        elif (TEMPLATES_DIR / "default.generators").exists():
            config_path = TEMPLATES_DIR / "default.generators"
        else:
            return get_default_generator()

    if not config_path.exists():
        return get_default_generator()

    with open(config_path) as f:
        data = yaml.safe_load(f)

    return GeneratorConfig(
        name=data.get("name", "generator"),
        provider_openai_base_url=data["provider_openai_base_url"],
        model=data["model"],
        api_key_env=data.get("api_key_env"),
        temperature=data.get("temperature", 0.7),
        max_tokens=data.get("max_tokens", 1000),
        input_cost_per_1m=data.get("input_cost_per_1m"),
        output_cost_per_1m=data.get("output_cost_per_1m"),
    )


def get_default_generator() -> GeneratorConfig:
    """Get default generator configuration"""
    return GeneratorConfig(
        name="default",
        provider_openai_base_url="https://api.openai.com/v1",
        model="gpt-4o-mini",
        api_key_env="OPENAI_API_KEY",
    )


def test_generator(generator: GeneratorConfig) -> dict[str, Any]:
    """Test if a generator is reachable and responding"""
    import time

    import httpx

    result = {
        "name": generator.name,
        "model": generator.model,
        "base_url": generator.provider_openai_base_url,
        "success": False,
        "error": None,
        "response_time_ms": None,
    }

    try:
        start = time.time()

        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{generator.provider_openai_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {generator.get_api_key() or 'unused'}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": generator.model,
                    "messages": [{"role": "user", "content": "Say OK"}],
                    "max_tokens": 10,
                },
            )

        elapsed_ms = int((time.time() - start) * 1000)
        result["response_time_ms"] = elapsed_ms

        if response.status_code == 200:
            result["success"] = True
        else:
            result["error"] = f"HTTP {response.status_code}: {response.text[:100]}"

    except httpx.ConnectError:
        result["error"] = "Connection refused - is the server running?"
    except httpx.TimeoutException:
        result["error"] = "Timeout - server took too long to respond"
    except Exception as e:
        result["error"] = str(e)

    return result


def test_active_generator(config_name: str = None) -> dict[str, Any]:
    """Test the generator from a config file"""
    if config_name:
        if not config_name.endswith(".generators"):
            config_name = f"{config_name}.generators"
        config_path = USER_CONFIG_DIR / config_name
        if not config_path.exists():
            return {
                "name": "Error",
                "model": "",
                "base_url": "",
                "success": False,
                "error": f"Config not found: {config_name}",
            }
        generator = load_generator_config(config_path)
    else:
        generator = load_generator_config()

    return test_generator(generator)
