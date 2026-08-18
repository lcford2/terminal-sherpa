"""Tests for OpenRouter provider."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from ask.config import SYSTEM_PROMPT
from ask.exceptions import APIError, AuthenticationError, RateLimitError
from ask.providers.openrouter import (
    BASH_COMMAND_TOOL,
    BASH_COMMAND_TOOL_CHOICE,
    OPENROUTER_BASE_URL,
    OpenRouterProvider,
)


def _mock_tool_call_response(arguments: dict) -> MagicMock:
    """Build a mock response containing a single forced tool call."""
    mock_tool_call = MagicMock()
    mock_tool_call.function.arguments = json.dumps(arguments)

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.tool_calls = [mock_tool_call]
    return mock_response


def test_openrouter_provider_init():
    """Test provider initialization."""
    config = {"model_name": "openrouter/auto"}
    provider = OpenRouterProvider(config)

    assert provider.config == config
    assert provider.client is None


def test_validate_config_success(mock_openrouter_key):
    """Test successful config validation."""
    config = {"api_key_env": "OPENROUTER_API_KEY"}
    provider = OpenRouterProvider(config)

    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        provider.validate_config()

        assert provider.client == mock_client
        mock_openai.assert_called_once_with(
            api_key="test-openrouter-key", base_url=OPENROUTER_BASE_URL
        )


def test_validate_config_custom_base_url(mock_openrouter_key):
    """Test custom base URL configuration."""
    config = {"base_url": "https://custom.openrouter.proxy/api/v1"}
    provider = OpenRouterProvider(config)

    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        provider.validate_config()

        mock_openai.assert_called_once_with(
            api_key="test-openrouter-key",
            base_url="https://custom.openrouter.proxy/api/v1",
        )


def test_validate_config_missing_key(mock_env_vars):
    """Test missing API key error."""
    config = {"api_key_env": "OPENROUTER_API_KEY"}
    provider = OpenRouterProvider(config)

    with pytest.raises(
        AuthenticationError, match="OPENROUTER_API_KEY environment variable is required"
    ):
        provider.validate_config()


def test_validate_config_custom_env():
    """Test custom environment variable."""
    config = {"api_key_env": "CUSTOM_OPENROUTER_KEY"}
    provider = OpenRouterProvider(config)

    with patch.dict(os.environ, {"CUSTOM_OPENROUTER_KEY": "custom-key"}):
        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            provider.validate_config()

            mock_openai.assert_called_once_with(
                api_key="custom-key", base_url=OPENROUTER_BASE_URL
            )


def test_get_default_config():
    """Test default configuration values."""
    default_config = OpenRouterProvider.get_default_config()

    assert default_config["model_name"] == "openrouter/auto"
    assert default_config["max_tokens"] == 150
    assert default_config["api_key_env"] == "OPENROUTER_API_KEY"
    assert default_config["base_url"] == OPENROUTER_BASE_URL
    assert default_config["temperature"] == 0.5
    assert default_config["system_prompt"] == SYSTEM_PROMPT


def test_get_bash_command_success(mock_openrouter_key):
    """Test successful command generation via forced tool call."""
    config = {"model_name": "openai/gpt-4o-mini", "max_tokens": 150}
    provider = OpenRouterProvider(config)

    mock_response = _mock_tool_call_response({"command": "ls -la"})

    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        result = provider.get_bash_command("list files")

        assert result == "ls -la"
        mock_client.chat.completions.create.assert_called_once_with(
            model="openai/gpt-4o-mini",
            max_completion_tokens=150,
            temperature=0.5,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "list files"},
            ],
            tools=[BASH_COMMAND_TOOL],
            tool_choice=BASH_COMMAND_TOOL_CHOICE,
        )


def test_get_bash_command_strips_whitespace(mock_openrouter_key):
    """Test that surrounding whitespace on the command is stripped."""
    config = {}
    provider = OpenRouterProvider(config)

    mock_response = _mock_tool_call_response({"command": "  ls -la  \n"})

    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        result = provider.get_bash_command("list files")

        assert result == "ls -la"


def test_get_bash_command_no_tool_calls(mock_openrouter_key):
    """Test handling when the model returns no tool call."""
    config = {}
    provider = OpenRouterProvider(config)

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.tool_calls = None

    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with pytest.raises(APIError, match="API returned empty response"):
            provider.get_bash_command("list files")


def test_get_bash_command_empty_command(mock_openrouter_key):
    """Test handling when the tool call has an empty command argument."""
    config = {}
    provider = OpenRouterProvider(config)

    mock_response = _mock_tool_call_response({"command": ""})

    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with pytest.raises(APIError, match="API returned empty response"):
            provider.get_bash_command("list files")


def test_get_bash_command_invalid_json(mock_openrouter_key):
    """Test handling when the tool call arguments are not valid JSON."""
    config = {}
    provider = OpenRouterProvider(config)

    mock_tool_call = MagicMock()
    mock_tool_call.function.arguments = "not valid json"

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.tool_calls = [mock_tool_call]

    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with pytest.raises(APIError, match="API returned invalid JSON"):
            provider.get_bash_command("list files")


def test_get_bash_command_auto_validate(mock_openrouter_key):
    """Test auto-validation behavior."""
    config = {}
    provider = OpenRouterProvider(config)

    mock_response = _mock_tool_call_response({"command": "ls -la"})

    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        assert provider.client is None

        result = provider.get_bash_command("list files")

        assert provider.client is not None
        assert result == "ls -la"


def test_handle_api_error_auth():
    """Test authentication error mapping."""
    provider = OpenRouterProvider({})

    with pytest.raises(AuthenticationError, match="Invalid API key"):
        provider._handle_api_error(Exception("authentication failed"))


def test_handle_api_error_rate_limit():
    """Test rate limit error mapping."""
    provider = OpenRouterProvider({})

    with pytest.raises(RateLimitError, match="API rate limit exceeded"):
        provider._handle_api_error(Exception("rate limit exceeded"))


def test_handle_api_error_generic():
    """Test generic API error mapping."""
    provider = OpenRouterProvider({})

    with pytest.raises(APIError, match="API request failed"):
        provider._handle_api_error(Exception("unexpected error"))
