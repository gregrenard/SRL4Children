"""Judge configuration"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

# Load judge API keys from srl4c/.env
SRL4C_ROOT = Path(__file__).parent.parent.parent.parent  # srl4c/
load_dotenv(SRL4C_ROOT / ".env")


@dataclass
class JudgeConfig:
    """Configuration for a single judge"""
    name: str
    provider_openai_base_url: str
    model: str
    api_key_env: Optional[str] = None
    temperature: float = 0.1

    def get_api_key(self) -> Optional[str]:
        """Get API key from environment (loaded from srl4c/.env)"""
        if self.api_key_env:
            return os.environ.get(self.api_key_env)
        return "unused"  # For Ollama


@dataclass
class JudgeSystemConfig:
    """Configuration for the judge system"""
    judges: list[JudgeConfig]
    n_passes: int = 3
    agreement_threshold: float = 0.8


def load_judge_config(config_path: Path = None) -> JudgeSystemConfig:
    """Load judge configuration from YAML file"""
    if config_path is None:
        # Try ~/.srl4c/judges.yaml first, then fall back to template
        user_config = Path.home() / ".srl4c" / "judges.yaml"
        template_config = SRL4C_ROOT / "templates" / "judges.yaml"

        if user_config.exists():
            config_path = user_config
        elif template_config.exists():
            config_path = template_config
        else:
            return get_default_config()

    if not config_path.exists():
        return get_default_config()

    with open(config_path) as f:
        data = yaml.safe_load(f)

    judges = []
    for name, jconf in data.get("judges", {}).items():
        judges.append(JudgeConfig(
            name=name,
            provider_openai_base_url=jconf["provider_openai_base_url"],
            model=jconf["model"],
            api_key_env=jconf.get("api_key_env"),
            temperature=jconf.get("temperature", 0.1),
        ))

    return JudgeSystemConfig(
        judges=judges,
        n_passes=data.get("n_passes", 3),
        agreement_threshold=data.get("consistency", {}).get("agreement_threshold", 0.8),
    )


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
