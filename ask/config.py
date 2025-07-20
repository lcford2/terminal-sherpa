"""Configuration loading and management module."""

import os
from pathlib import Path
from typing import Any

import ollama
import toml
from loguru import logger

from ask.exceptions import ConfigurationError

SYSTEM_PROMPT = (
    "You are a bash command generator. Given a user request, "
    "respond with ONLY the bash command that accomplishes the task. "
    "Do not include explanations, comments, or any other text. "
    "Just the command.",
)


module_logger = logger.bind(module=__name__)


def get_config_path() -> Path | None:  # pragma: no mutate
    """Find config file using XDG standard."""
    # Primary location: $XDG_CONFIG_HOME/ask/config.toml
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        module_logger.debug(f"XDG_CONFIG_HOME: {xdg_config_home}")
        primary_path = Path(xdg_config_home) / "ask" / "config.toml"
    else:
        module_logger.debug("XDG_CONFIG_HOME not set, using default")
        primary_path = Path.home() / ".config" / "ask" / "config.toml"

    if primary_path.exists():
        module_logger.debug(f"Primary path exists: {primary_path}")
        return primary_path

    # Fallback location: ~/.ask/config.toml
    fallback_path = Path.home() / ".ask" / "config.toml"
    if fallback_path.exists():
        module_logger.debug(f"Fallback path exists: {fallback_path}")
        return fallback_path

    return None


def load_config() -> dict[str, Any]:
    """Load configuration from TOML file."""
    config_path = get_config_path()
    module_logger.debug(f"Config path: {config_path}")
    if config_path is None:
        module_logger.warning("No config path found")
        return {}

    try:
        with open(config_path) as f:
            return toml.load(f)
    except Exception as e:
        raise ConfigurationError(f"Failed to load config file {config_path}: {e}")


def get_provider_config(
    config: dict[str, Any], provider_spec: str
) -> tuple[str, dict[str, Any]]:
    """Parse provider:model syntax and return provider name and config."""
    if ":" in provider_spec:
        provider_name, model_name = provider_spec.split(":", 1)
        # First try to get nested config (e.g., anthropic.haiku)
        provider_section = config.get(provider_name, {})
        if isinstance(provider_section, dict) and model_name in provider_section:
            provider_config = provider_section[model_name]
        else:
            module_logger.warning(
                f"Model {model_name} not found in provider {provider_name}, "
                "falling back to base provider config"
            )
            # Fall back to base provider config
            provider_config = provider_section
    else:
        provider_name = provider_spec
        provider_config = config.get(provider_name, {})

    # Add global settings
    global_config = config.get("ask", {})

    # Merge global and provider-specific config
    merged_config = {**global_config, **provider_config}

    return provider_name, merged_config


def get_default_model(config: dict[str, Any]) -> str | None:  # pragma: no mutate
    """Get default model from configuration."""
    global_config = config.get("ask", {})
    return global_config.get("default_model")


def check_ollama_available() -> bool:
    """Check if Ollama is available."""
    try:
        ollama.list()
        return True
    except ConnectionError as e:
        module_logger.warning(f"Ollama is not available: {e}")
        return False


def get_default_provider() -> str | None:  # pragma: no mutate
    """Determine fallback provider from environment variables."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    elif os.environ.get("OPENAI_API_KEY"):
        return "openai"
    elif os.environ.get("GEMINI_API_KEY"):
        return "gemini"
    elif os.environ.get("GROK_API_KEY"):
        return "grok"
    elif check_ollama_available():
        return "ollama"

    return None
