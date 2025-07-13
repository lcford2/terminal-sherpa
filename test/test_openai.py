"""Tests for OpenAI provider."""

import os
import re
from unittest.mock import MagicMock, patch

import pytest

from ask.config import SYSTEM_PROMPT
from ask.exceptions import APIError, AuthenticationError, RateLimitError
from ask.providers.openai import OpenAIProvider


def test_openai_provider_init():
    """Test provider initialization."""
    config = {"model_name": "gpt-4o-mini"}
    provider = OpenAIProvider(config)

    assert provider.config == config
    assert provider.client is None


def test_validate_config_success(mock_openai_key):
    """Test successful config validation."""
    config = {"api_key_env": "OPENAI_API_KEY"}
    provider = OpenAIProvider(config)

    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        provider.validate_config()

        assert provider.client == mock_client
        mock_openai.assert_called_once_with(api_key="test-openai-key")


def test_validate_config_missing_key(mock_env_vars):
    """Test missing API key error."""
    config = {"api_key_env": "OPENAI_API_KEY"}
    provider = OpenAIProvider(config)

    with pytest.raises(
        AuthenticationError, match="OPENAI_API_KEY environment variable is required"
    ):
        provider.validate_config()


def test_validate_config_custom_env():
    """Test custom environment variable."""
    config = {"api_key_env": "CUSTOM_OPENAI_KEY"}
    provider = OpenAIProvider(config)

    with patch.dict(os.environ, {"CUSTOM_OPENAI_KEY": "custom-key"}):
        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            provider.validate_config()

            mock_openai.assert_called_once_with(api_key="custom-key")


def test_get_default_config():
    """Test default configuration values."""
    default_config = OpenAIProvider.get_default_config()

    assert default_config["model_name"] == "gpt-4o-mini"
    assert default_config["max_tokens"] == 150
    assert default_config["api_key_env"] == "OPENAI_API_KEY"
    assert default_config["temperature"] == 0.0
    assert default_config["system_prompt"] == SYSTEM_PROMPT


def test_get_bash_command_success(mock_openai_key):
    """Test successful command generation."""
    config = {"model_name": "gpt-4o-mini", "max_tokens": 150}
    provider = OpenAIProvider(config)

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "ls -la"

    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        result = provider.get_bash_command("list files")

        assert result == "ls -la"
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4o-mini",
            max_completion_tokens=150,
            temperature=0.0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "list files"},
            ],
        )


def test_get_bash_command_with_code_block(mock_openai_key):
    """Test bash code block extraction."""
    config = {}
    provider = OpenAIProvider(config)

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "```bash\nls -la\n```"

    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        result = provider.get_bash_command("list files")

        assert result == "ls -la"


def test_get_bash_command_without_code_block(mock_openai_key):
    """Test plain text response."""
    config = {}
    provider = OpenAIProvider(config)

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "ls -la"

    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        result = provider.get_bash_command("list files")

        assert result == "ls -la"


def test_get_bash_command_empty_response(mock_openai_key):
    """Test empty API response handling."""
    config = {}
    provider = OpenAIProvider(config)

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = None

    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with pytest.raises(APIError, match="API returned empty response"):
            provider.get_bash_command("list files")


def test_get_bash_command_auto_validate(mock_openai_key):
    """Test auto-validation behavior."""
    config = {}
    provider = OpenAIProvider(config)

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "ls -la"

    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        # Client should be None initially
        assert provider.client is None

        result = provider.get_bash_command("list files")

        # Client should be set after auto-validation
        assert provider.client is not None
        assert result == "ls -la"


def test_handle_api_error_auth():
    """Test authentication error mapping."""
    provider = OpenAIProvider({})

    with pytest.raises(AuthenticationError, match="Invalid API key"):
        provider._handle_api_error(Exception("authentication failed"))


def test_handle_api_error_rate_limit():
    """Test rate limit error mapping."""
    provider = OpenAIProvider({})

    with pytest.raises(RateLimitError, match="API rate limit exceeded"):
        provider._handle_api_error(Exception("rate limit exceeded"))


def test_handle_api_error_quota():
    """Test quota error mapping."""
    provider = OpenAIProvider({})

    with pytest.raises(RateLimitError, match="API rate limit exceeded"):
        provider._handle_api_error(Exception("quota exceeded"))


def test_handle_api_error_generic():
    """Test generic API error mapping."""
    provider = OpenAIProvider({})

    with pytest.raises(APIError, match="API request failed"):
        provider._handle_api_error(Exception("unexpected error"))


def test_config_parameter_usage(mock_openai_key):
    """Test configuration parameter usage."""
    config = {
        "model_name": "gpt-4o",
        "max_tokens": 1024,
        "temperature": 0.5,
        "system_prompt": "Custom system prompt",
    }
    provider = OpenAIProvider(config)

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "custom response"

    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        result = provider.get_bash_command("test prompt")

        assert result == "custom response"
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4o",
            max_completion_tokens=1024,
            temperature=0.5,
            messages=[
                {"role": "system", "content": "Custom system prompt"},
                {"role": "user", "content": "test prompt"},
            ],
        )


def test_regex_bash_extraction():
    """Test regex pattern for bash code extraction."""
    _ = OpenAIProvider({})

    # Test various bash code block formats
    test_cases = [
        ("```bash\nls -la\n```", "ls -la"),
        ("```bash\nfind . -name '*.py'\n```", "find . -name '*.py'"),
        ("Here is the command:\n```bash\necho 'hello'\n```", "echo 'hello'"),
        ("plain text command", "plain text command"),
        ("```python\nprint('hello')\n```", "```python\nprint('hello')\n```"),
    ]

    for input_text, expected in test_cases:
        # Test the regex pattern used in the provider
        re_match = re.search(r"```bash\n(.*)\n```", input_text)
        if re_match:
            result = re_match.group(1)
        else:
            result = input_text

        assert result == expected
