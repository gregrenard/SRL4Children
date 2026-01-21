"""Judge configuration"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from srl4c.paths import PROJECT_ROOT, TEMPLATES_DIR, USER_CONFIG_DIR

# Load judge API keys from .env
load_dotenv(PROJECT_ROOT / ".env")


@dataclass
class JudgeConfig:
    """Configuration for a single judge"""

    name: str
    provider_openai_base_url: str
    model: str
    api_key_env: str | None = None
    temperature: float = 0.1
    input_cost_per_1m: float | None = None  # Cost per 1M input tokens (USD)
    output_cost_per_1m: float | None = None  # Cost per 1M output tokens (USD)

    def get_api_key(self) -> str | None:
        """Get API key from environment (loaded from srl4c/.env)"""
        if self.api_key_env:
            return os.environ.get(self.api_key_env)
        return "unused"  # For Ollama

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float | None:
        """Calculate cost for a request. Returns None if pricing not configured."""
        if self.input_cost_per_1m is None or self.output_cost_per_1m is None:
            return None
        input_cost = (input_tokens / 1_000_000) * self.input_cost_per_1m
        output_cost = (output_tokens / 1_000_000) * self.output_cost_per_1m
        return input_cost + output_cost


@dataclass
class JudgeSystemConfig:
    """Configuration for the judge system"""

    judges: list[JudgeConfig]
    n_passes: int = 3
    agreement_threshold: float = 0.8
    hyperparameters: dict = None  # pass_idx -> {temperature, top_p}

    def __post_init__(self):
        if self.hyperparameters is None:
            # Default hyperparameters for 3 passes
            self.hyperparameters = {
                0: {"temperature": 0.1, "top_p": 0.9},
                1: {"temperature": 0.2, "top_p": 0.95},
                2: {"temperature": 0.15, "top_p": 0.92},
            }

    def get_hyperparams(self, pass_idx: int) -> dict:
        """Get hyperparameters for a specific pass"""
        return self.hyperparameters.get(pass_idx, {"temperature": 0.1, "top_p": 0.9})


def get_settings() -> dict[str, Any]:
    """Load settings from ~/.srl4c/settings.yaml"""
    settings_path = USER_CONFIG_DIR / "settings.yaml"
    if settings_path.exists():
        with open(settings_path) as f:
            return yaml.safe_load(f) or {}
    return {"active_judges": "default.judges"}


def set_active_judges(filename: str) -> None:
    """Set the active judges file in settings"""
    settings = get_settings()
    settings["active_judges"] = filename
    settings_path = USER_CONFIG_DIR / "settings.yaml"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_path, "w") as f:
        yaml.dump(settings, f)


def get_active_judges_file() -> str:
    """Get the currently active judges filename"""
    return get_settings().get("active_judges", "default.judges")


def list_judge_files() -> list[dict[str, Any]]:
    """List all available .judges files with metadata"""
    judge_files = []

    # Check user config directory
    if USER_CONFIG_DIR.exists():
        for f in USER_CONFIG_DIR.glob("*.judges"):
            try:
                with open(f) as fp:
                    data = yaml.safe_load(fp) or {}
                judge_count = len(data.get("judges", {}))
                n_passes = data.get("n_passes", 1)
                judge_files.append(
                    {
                        "name": f.name,
                        "path": str(f),
                        "judges_count": judge_count,
                        "n_passes": n_passes,
                        "is_active": f.name == get_active_judges_file(),
                    }
                )
            except Exception:
                judge_files.append(
                    {
                        "name": f.name,
                        "path": str(f),
                        "judges_count": 0,
                        "n_passes": 0,
                        "is_active": f.name == get_active_judges_file(),
                        "error": "Failed to parse",
                    }
                )

    return sorted(judge_files, key=lambda x: x["name"])


def get_judge_file_content(filename: str) -> str | None:
    """Get the raw content of a judges file"""
    path = USER_CONFIG_DIR / filename
    if path.exists() and path.suffix == ".judges":
        return path.read_text()
    return None


def load_judge_config(config_path: Path = None) -> JudgeSystemConfig:
    """Load judge configuration from .judges file"""
    if config_path is None:
        # Get active judges file from settings
        active_file = get_active_judges_file()
        user_config = USER_CONFIG_DIR / active_file

        # Fallback chain: active file -> default.judges -> template
        if user_config.exists():
            config_path = user_config
        elif (USER_CONFIG_DIR / "default.judges").exists():
            config_path = USER_CONFIG_DIR / "default.judges"
        elif (TEMPLATES_DIR / "default.judges").exists():
            config_path = TEMPLATES_DIR / "default.judges"
        else:
            return get_default_config()

    if not config_path.exists():
        return get_default_config()

    with open(config_path) as f:
        data = yaml.safe_load(f)

    judges = []
    for name, jconf in data.get("judges", {}).items():
        judges.append(
            JudgeConfig(
                name=name,
                provider_openai_base_url=jconf["provider_openai_base_url"],
                model=jconf["model"],
                api_key_env=jconf.get("api_key_env"),
                temperature=jconf.get("temperature", 0.1),
                input_cost_per_1m=jconf.get("input_cost_per_1m"),
                output_cost_per_1m=jconf.get("output_cost_per_1m"),
            )
        )

    # Parse hyperparameters: convert pass_1, pass_2, etc. to 0, 1, 2
    hyperparameters = None
    if "hyperparameters" in data:
        hyperparameters = {}
        for key, params in data["hyperparameters"].items():
            # Extract pass number from "pass_1", "pass_2", etc.
            if key.startswith("pass_"):
                pass_idx = int(key.split("_")[1]) - 1  # Convert to 0-indexed
                hyperparameters[pass_idx] = params

    return JudgeSystemConfig(
        judges=judges,
        n_passes=data.get("n_passes", 3),
        agreement_threshold=data.get("consistency", {}).get("agreement_threshold", 0.8),
        hyperparameters=hyperparameters,
    )


def test_judge(judge: JudgeConfig) -> dict[str, Any]:
    """Test if a judge is reachable and responding"""
    import httpx

    result = {
        "name": judge.name,
        "model": judge.model,
        "base_url": judge.provider_openai_base_url,
        "success": False,
        "error": None,
        "response_time_ms": None,
    }

    try:
        import time

        start = time.time()

        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{judge.provider_openai_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {judge.get_api_key() or 'unused'}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": judge.model,
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


def test_all_judges(config_name: str = None) -> list[dict[str, Any]]:
    """Test all judges in a config file (default: active config)"""
    if config_name:
        # Load specific config
        if not config_name.endswith(".judges"):
            config_name = f"{config_name}.judges"
        config_path = USER_CONFIG_DIR / config_name
        if not config_path.exists():
            return [
                {
                    "name": "Error",
                    "model": "",
                    "base_url": "",
                    "success": False,
                    "error": f"Config not found: {config_name}",
                }
            ]
        config = load_judge_config(config_path)
    else:
        config = load_judge_config()

    results = []
    for judge in config.judges:
        results.append(test_judge(judge))
    return results


def get_default_config() -> JudgeSystemConfig:
    """Get default judge configuration (single OpenAI judge)"""
    return JudgeSystemConfig(
        judges=[
            JudgeConfig(
                name="judge_default",
                provider_openai_base_url="https://api.openai.com/v1",
                model="gpt-4o-mini",
                api_key_env="OPENAI_API_KEY",
            )
        ],
        n_passes=1,  # Single pass for simple default
    )


def create_default_judge_config(config_path: Path = None):
    """Create a default judges.yaml file"""
    if config_path is None:
        config_path = Path.home() / ".srl4c" / "judges.yaml"

    config_path.parent.mkdir(parents=True, exist_ok=True)

    default_yaml = """# SRL4C Judge Configuration
# Configure one or more judges for evaluating AI responses

# Number of evaluation passes per judge (for consistency)
n_passes: 1

# Minimum agreement between judges (0.0 - 1.0)
agreement_threshold: 0.8

# Judge definitions
judges:
  # Example: OpenAI judge
  judge_openai:
    provider_openai_base_url: https://api.openai.com/v1
    model: gpt-4o-mini
    api_key_env: OPENAI_API_KEY
    temperature: 0.1

  # Example: Local Ollama judge (uncomment to use)
  # judge_ollama:
  #   provider_openai_base_url: http://localhost:11434/v1
  #   model: qwen3:8b
  #   api_key_env: null
  #   temperature: 0.1

  # Example: DeepInfra judge (uncomment to use)
  # judge_deepinfra:
  #   provider_openai_base_url: https://api.deepinfra.com/v1/openai
  #   model: meta-llama/Llama-3.3-70B-Instruct
  #   api_key_env: DEEPINFRA_API_KEY
  #   temperature: 0.1
"""

    config_path.write_text(default_yaml)
    return config_path
