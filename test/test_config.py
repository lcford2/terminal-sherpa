"""Tests for the configuration system."""

import os
from unittest.mock import patch

import pytest

from ask.config import (
    get_config_path,
    get_default_model,
    get_default_provider,
    get_provider_config,
    load_config,
)
from ask.exceptions import ConfigurationError


def test_get_config_path_xdg_config_home(temp_config_dir):
    """Test XDG_CONFIG_HOME path resolution."""
    config_file = temp_config_dir / "ask" / "config.toml"
    config_file.parent.mkdir(parents=True)
    config_file.touch()

    with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(temp_config_dir)}):
        assert get_config_path() == config_file


def test_get_config_path_default_xdg(temp_config_dir):
    """Test default ~/.config path."""
    config_file = temp_config_dir / ".config" / "ask" / "config.toml"
    config_file.parent.mkdir(parents=True)
    config_file.touch()

    with patch.dict(os.environ, {}, clear=True):
        with patch("pathlib.Path.home", return_value=temp_config_dir):
            assert get_config_path() == config_file


def test_get_config_path_fallback(temp_config_dir):
    """Test ~/.ask fallback path."""
    config_file = temp_config_dir / ".ask" / "config.toml"
    config_file.parent.mkdir(parents=True)
    config_file.touch()

    with patch.dict(os.environ, {}, clear=True):
        with patch("pathlib.Path.home", return_value=temp_config_dir):
            assert get_config_path() == config_file


def test_get_config_path_none(temp_config_dir):
    """Test when no config file exists."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("pathlib.Path.home", return_value=temp_config_dir):
            assert get_config_path() is None


def test_load_config_valid(test_resources_dir):
    """Test loading valid TOML config."""
    config_file = test_resources_dir / "valid_config.toml"

    with patch("ask.config.get_config_path", return_value=config_file):
        config = load_config()
        assert config["ask"]["default_model"] == "anthropic"
        assert config["anthropic"]["model_name"] == "claude-3-haiku-20240307"


def test_load_config_invalid(test_resources_dir):
    """Test loading invalid TOML syntax."""
    config_file = test_resources_dir / "invalid_config.toml"

    with patch("ask.config.get_config_path", return_value=config_file):
        with pytest.raises(ConfigurationError, match="Failed to load config file"):
            load_config()


def test_load_config_not_found():
    """Test when config file doesn't exist."""
    with patch("ask.config.get_config_path", return_value=None):
        config = load_config()
        assert config == {}


def test_load_config_permission_error(temp_config_dir):
    """Test permission errors."""
    config_file = temp_config_dir / "config.toml"
    config_file.touch()

    with patch("ask.config.get_config_path", return_value=config_file):
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(ConfigurationError, match="Failed to load config file"):
                load_config()


def test_get_provider_config_simple():
    """Test simple provider name parsing."""
    config = {"anthropic": {"model_name": "claude-3-haiku-20240307"}}

    provider_name, provider_config = get_provider_config(config, "anthropic")
    assert provider_name == "anthropic"
    assert provider_config["model_name"] == "claude-3-haiku-20240307"


def test_get_provider_config_with_model():
    """Test provider:model syntax."""
    config = {
        "anthropic": {
            "model_name": "claude-3-haiku-20240307",
            "sonnet": {"model_name": "claude-3-5-sonnet-20241022"},
        }
    }

    provider_name, provider_config = get_provider_config(config, "anthropic:sonnet")
    assert provider_name == "anthropic"
    assert provider_config["model_name"] == "claude-3-5-sonnet-20241022"


def test_get_provider_config_nested():
    """Test nested provider configuration."""
    config = {
        "anthropic": {
            "base_setting": "base_value",
            "sonnet": {"model_name": "claude-3-5-sonnet-20241022", "max_tokens": 1024},
        }
    }

    provider_name, provider_config = get_provider_config(config, "anthropic:sonnet")
    assert provider_name == "anthropic"
    assert provider_config["model_name"] == "claude-3-5-sonnet-20241022"
    assert provider_config["max_tokens"] == 1024


def test_get_provider_config_global_merge():
    """Test global config merging."""
    config = {
        "ask": {"global_setting": "global_value", "temperature": 0.1},
        "anthropic": {"model_name": "claude-3-haiku-20240307", "temperature": 0.0},
    }

    provider_name, provider_config = get_provider_config(config, "anthropic")
    assert provider_name == "anthropic"
    assert provider_config["global_setting"] == "global_value"
    assert provider_config["temperature"] == 0.0  # Provider-specific overrides global


def test_get_default_model():
    """Test default model retrieval."""
    config = {"ask": {"default_model": "anthropic:sonnet"}}

    assert get_default_model(config) == "anthropic:sonnet"


def test_get_default_provider_anthropic(mock_anthropic_key):
    """Test Anthropic as default provider."""
    assert get_default_provider() == "anthropic"


def test_get_default_provider_openai(mock_openai_key):
    """Test OpenAI as default provider."""
    assert get_default_provider() == "openai"


def test_get_default_provider_none(mock_env_vars):
    """Test when no API keys available."""
    assert get_default_provider() is None
