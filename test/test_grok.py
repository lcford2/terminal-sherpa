"""Tests for Grok provider using xAI SDK."""

import os
from unittest.mock import MagicMock, patch

import pytest

from ask.config import SYSTEM_PROMPT
from ask.exceptions import APIError, AuthenticationError, RateLimitError
from ask.providers.grok import GrokProvider


def test_grok_provider_init():
    """Test provider initialization."""
    config = {"model_name": "grok-3-fast"}
    provider = GrokProvider(config)

    assert provider.config == config
    assert provider.client is None


def test_validate_config_success(mock_grok_key):
    """Test successful config validation."""
    config = {"api_key_env": "XAI_API_KEY"}
    provider = GrokProvider(config)

    with patch("ask.providers.grok.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        provider.validate_config()

        assert provider.client == mock_client
        mock_client_class.assert_called_once_with(api_key="test-grok-key")


def test_validate_config_missing_key(mock_env_vars):
    """Test missing API key error."""
    config = {"api_key_env": "XAI_API_KEY"}
    provider = GrokProvider(config)

    with pytest.raises(
        AuthenticationError, match="XAI_API_KEY environment variable is required"
    ):
        provider.validate_config()


def test_validate_config_custom_env():
    """Test custom environment variable."""
    config = {"api_key_env": "CUSTOM_XAI_KEY"}
    provider = GrokProvider(config)

    with patch.dict(os.environ, {"CUSTOM_XAI_KEY": "custom-xai-key"}):
        with patch("ask.providers.grok.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            provider.validate_config()

            assert provider.client == mock_client
            mock_client_class.assert_called_once_with(api_key="custom-xai-key")


@patch("ask.providers.grok.system")
@patch("ask.providers.grok.user")
def test_get_bash_command_success(mock_user, mock_system, mock_grok_key):
    """Test successful bash command generation."""
    config = {"model_name": "grok-beta", "max_tokens": 150}
    provider = GrokProvider(config)

    # Mock the xAI SDK workflow components
    mock_chat = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "ls -la"
    mock_chat.sample.return_value = mock_response

    mock_system_msg = MagicMock()
    mock_user_msg = MagicMock()
    mock_system.return_value = mock_system_msg
    mock_user.return_value = mock_user_msg

    with patch("ask.providers.grok.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client.chat.create.return_value = mock_chat
        mock_client_class.return_value = mock_client
        provider.client = mock_client

        result = provider.get_bash_command("list files")

        assert result == "ls -la"
        mock_client.chat.create.assert_called_once_with(model="grok-beta")
        mock_system.assert_called_once_with(SYSTEM_PROMPT)
        mock_user.assert_called_once_with("list files")
        assert mock_chat.append.call_count == 2
        mock_chat.append.assert_any_call(mock_system_msg)
        mock_chat.append.assert_any_call(mock_user_msg)
        mock_chat.sample.assert_called_once()


@patch("ask.providers.grok.system")
@patch("ask.providers.grok.user")
def test_get_bash_command_with_code_block(mock_user, mock_system, mock_grok_key):
    """Test bash command extraction from code block."""
    config = {}
    provider = GrokProvider(config)

    # Mock the xAI SDK workflow components
    mock_chat = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "```bash\nls -la\n```"
    mock_chat.sample.return_value = mock_response

    mock_system_msg = MagicMock()
    mock_user_msg = MagicMock()
    mock_system.return_value = mock_system_msg
    mock_user.return_value = mock_user_msg

    with patch("ask.providers.grok.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client.chat.create.return_value = mock_chat
        mock_client_class.return_value = mock_client
        provider.client = mock_client

        result = provider.get_bash_command("list files")

        assert result == "ls -la"


@patch("ask.providers.grok.system")
@patch("ask.providers.grok.user")
def test_get_bash_command_empty_response(mock_user, mock_system, mock_grok_key):
    """Test handling of empty API response."""
    config = {}
    provider = GrokProvider(config)

    # Mock the xAI SDK workflow components
    mock_chat = MagicMock()
    mock_response = MagicMock()
    mock_response.content = None
    mock_chat.sample.return_value = mock_response

    mock_system_msg = MagicMock()
    mock_user_msg = MagicMock()
    mock_system.return_value = mock_system_msg
    mock_user.return_value = mock_user_msg

    with patch("ask.providers.grok.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client.chat.create.return_value = mock_chat
        mock_client_class.return_value = mock_client
        provider.client = mock_client

        with pytest.raises(APIError, match="API returned empty response"):
            provider.get_bash_command("list files")


def test_handle_authentication_error(mock_grok_key):
    """Test authentication error handling."""
    config = {}
    provider = GrokProvider(config)

    with patch("ask.providers.grok.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client.chat.create.side_effect = Exception("Authentication failed")
        mock_client_class.return_value = mock_client
        provider.client = mock_client

        with pytest.raises(AuthenticationError, match="Invalid API key"):
            provider.get_bash_command("test")


def test_handle_rate_limit_error(mock_grok_key):
    """Test rate limit error handling."""
    config = {}
    provider = GrokProvider(config)

    with patch("ask.providers.grok.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client.chat.create.side_effect = Exception("Rate limit exceeded")
        mock_client_class.return_value = mock_client
        provider.client = mock_client

        with pytest.raises(RateLimitError, match="rate limit exceeded"):
            provider.get_bash_command("test")


def test_handle_general_api_error(mock_grok_key):
    """Test general API error handling."""
    config = {}
    provider = GrokProvider(config)

    with patch("ask.providers.grok.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client.chat.create.side_effect = Exception("Unknown error")
        mock_client_class.return_value = mock_client
        provider.client = mock_client

        with pytest.raises(APIError, match="API request failed - Unknown error"):
            provider.get_bash_command("test")


def test_get_default_config():
    """Test default configuration."""
    default_config = GrokProvider.get_default_config()

    expected_config = {
        "model_name": "grok-3-fast",
        "max_tokens": 150,
        "api_key_env": "XAI_API_KEY",
        "temperature": 0.0,
        "system_prompt": SYSTEM_PROMPT,
    }

    assert default_config == expected_config


@patch("ask.providers.grok.system")
@patch("ask.providers.grok.user")
def test_get_bash_command_multiline_code_block(mock_user, mock_system, mock_grok_key):
    """Test bash command extraction from multiline code block."""
    config = {}
    provider = GrokProvider(config)

    # Mock the xAI SDK workflow components
    mock_chat = MagicMock()
    mock_response = MagicMock()
    mock_response.content = (
        "```bash\nfind . -name '*.py' \\\n  "
        "-type f \\\n  -exec grep -l 'test' {} \\;\n```"
    )
    mock_chat.sample.return_value = mock_response

    mock_system_msg = MagicMock()
    mock_user_msg = MagicMock()
    mock_system.return_value = mock_system_msg
    mock_user.return_value = mock_user_msg

    with patch("ask.providers.grok.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client.chat.create.return_value = mock_chat
        mock_client_class.return_value = mock_client
        provider.client = mock_client

        result = provider.get_bash_command("find Python files with test")

        expected = "find . -name '*.py' \\\n  -type f \\\n  -exec grep -l 'test' {} \\;"
        assert result == expected
