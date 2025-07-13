"""Tests for Anthropic provider."""

import os
from unittest.mock import MagicMock, patch

import pytest

from ask.config import SYSTEM_PROMPT
from ask.exceptions import APIError, AuthenticationError, RateLimitError
from ask.providers.anthropic import AnthropicProvider


def test_anthropic_provider_init():
    """Test provider initialization."""
    config = {"model_name": "claude-3-haiku-20240307"}
    provider = AnthropicProvider(config)

    assert provider.config == config
    assert provider.client is None


def test_validate_config_success(mock_anthropic_key):
    """Test successful config validation."""
    config = {"api_key_env": "ANTHROPIC_API_KEY"}
    provider = AnthropicProvider(config)

    with patch("anthropic.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        provider.validate_config()

        assert provider.client == mock_client
        mock_anthropic.assert_called_once_with(api_key="test-anthropic-key")


def test_validate_config_missing_key(mock_env_vars):
    """Test missing API key error."""
    config = {"api_key_env": "ANTHROPIC_API_KEY"}
    provider = AnthropicProvider(config)

    with pytest.raises(
        AuthenticationError, match="ANTHROPIC_API_KEY environment variable is required"
    ):
        provider.validate_config()


def test_validate_config_custom_env():
    """Test custom environment variable."""
    config = {"api_key_env": "CUSTOM_ANTHROPIC_KEY"}
    provider = AnthropicProvider(config)

    with patch.dict(os.environ, {"CUSTOM_ANTHROPIC_KEY": "custom-key"}):
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client

            provider.validate_config()

            mock_anthropic.assert_called_once_with(api_key="custom-key")


def test_get_default_config():
    """Test default configuration values."""
    default_config = AnthropicProvider.get_default_config()

    assert default_config["model_name"] == "claude-3-haiku-20240307"
    assert default_config["max_tokens"] == 150
    assert default_config["api_key_env"] == "ANTHROPIC_API_KEY"
    assert default_config["temperature"] == 0.0
    assert default_config["system_prompt"] == SYSTEM_PROMPT


def test_get_bash_command_success(mock_anthropic_key):
    """Test successful command generation."""
    config = {"model_name": "claude-3-haiku-20240307", "max_tokens": 150}
    provider = AnthropicProvider(config)

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="ls -la")]

    with patch("anthropic.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        result = provider.get_bash_command("list files")

        assert result == "ls -la"
        mock_client.messages.create.assert_called_once_with(
            model="claude-3-haiku-20240307",
            max_tokens=150,
            temperature=0.0,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": "list files"}],
        )


def test_get_bash_command_auto_validate(mock_anthropic_key):
    """Test auto-validation behavior."""
    config = {}
    provider = AnthropicProvider(config)

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="ls -la")]

    with patch("anthropic.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        # Client should be None initially
        assert provider.client is None

        result = provider.get_bash_command("list files")

        # Client should be set after auto-validation
        assert provider.client is not None
        assert result == "ls -la"


def test_handle_api_error_auth():
    """Test authentication error mapping."""
    provider = AnthropicProvider({})

    with pytest.raises(AuthenticationError, match="Invalid API key"):
        provider._handle_api_error(Exception("authentication failed"))


def test_handle_api_error_rate_limit():
    """Test rate limit error mapping."""
    provider = AnthropicProvider({})

    with pytest.raises(RateLimitError, match="API rate limit exceeded"):
        provider._handle_api_error(Exception("rate limit exceeded"))


def test_handle_api_error_generic():
    """Test generic API error mapping."""
    provider = AnthropicProvider({})

    with pytest.raises(APIError, match="API request failed"):
        provider._handle_api_error(Exception("unexpected error"))


def test_config_parameter_usage(mock_anthropic_key):
    """Test configuration parameter usage."""
    config = {
        "model_name": "claude-3-5-sonnet-20241022",
        "max_tokens": 1024,
        "temperature": 0.5,
        "system_prompt": "Custom system prompt",
    }
    provider = AnthropicProvider(config)

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="custom response")]

    with patch("anthropic.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        result = provider.get_bash_command("test prompt")

        assert result == "custom response"
        mock_client.messages.create.assert_called_once_with(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            temperature=0.5,
            system="Custom system prompt",
            messages=[{"role": "user", "content": "test prompt"}],
        )
