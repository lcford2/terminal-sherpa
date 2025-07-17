"""Tests for Gemini provider."""

import os
from unittest.mock import MagicMock, patch

import pytest
from google.genai.types import GenerateContentConfig

from ask.config import SYSTEM_PROMPT
from ask.exceptions import APIError, AuthenticationError, RateLimitError
from ask.providers.gemini import GeminiProvider


def test_gemini_provider_init():
    """Test provider initialization."""
    config = {"model_name": "gemini-2.5-flash"}
    provider = GeminiProvider(config)

    assert provider.config == config
    assert provider.client is None


def test_validate_config_success(mock_gemini_key):
    """Test successful config validation."""
    config = {"api_key_env": "GEMINI_API_KEY"}
    provider = GeminiProvider(config)

    with patch("google.genai.Client") as mock_genai:
        mock_client = MagicMock()
        mock_genai.return_value = mock_client

        provider.validate_config()

        assert provider.client == mock_client
        mock_genai.assert_called_once_with(api_key="test-gemini-key")


def test_validate_config_missing_key(mock_env_vars):
    """Test missing API key error."""
    config = {"api_key_env": "GEMINI_API_KEY"}
    provider = GeminiProvider(config)

    with pytest.raises(
        AuthenticationError, match="GEMINI_API_KEY environment variable is required"
    ):
        provider.validate_config()


def test_validate_config_custom_env():
    """Test custom environment variable."""
    config = {"api_key_env": "CUSTOM_GEMINI_KEY"}
    provider = GeminiProvider(config)

    with patch.dict(os.environ, {"CUSTOM_GEMINI_KEY": "custom-key"}):
        with patch("google.genai.Client") as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client

            provider.validate_config()

            mock_genai.assert_called_once_with(api_key="custom-key")


def test_get_default_config():
    """Test default configuration values."""
    default_config = GeminiProvider.get_default_config()

    assert default_config["model_name"] == "gemini-2.5-flash"
    assert default_config["max_tokens"] == 150
    assert default_config["api_key_env"] == "GEMINI_API_KEY"
    assert default_config["temperature"] == 0.0
    assert default_config["system_prompt"] == SYSTEM_PROMPT


def test_parse_response_empty_candidates():
    """Test _parse_response with empty candidates."""
    provider = GeminiProvider({})

    # Test with None candidates
    mock_response = MagicMock()
    mock_response.candidates = None
    result = provider._parse_response(mock_response)
    assert result == ""

    # Test with empty candidates list
    mock_response.candidates = []
    result = provider._parse_response(mock_response)
    assert result == ""


def test_parse_response_none_parts():
    """Test _parse_response with None parts."""
    provider = GeminiProvider({})

    mock_response = MagicMock()
    mock_response.candidates = [MagicMock()]
    mock_response.candidates[0].content = MagicMock()
    mock_response.candidates[0].content.parts = None

    result = provider._parse_response(mock_response)
    assert result == ""


def test_parse_response_success():
    """Test _parse_response with successful response."""
    provider = GeminiProvider({})

    mock_response = MagicMock()
    mock_response.candidates = [MagicMock()]
    mock_response.candidates[0].content = MagicMock()
    mock_response.candidates[0].content.parts = [
        MagicMock(text="part1"),
        MagicMock(text="part2"),
    ]

    result = provider._parse_response(mock_response)
    assert result == "part1part2"


def test_get_bash_command_success(mock_gemini_key):
    """Test successful command generation."""
    config = {"model_name": "gemini-2.5-flash", "max_tokens": 150}
    provider = GeminiProvider(config)

    mock_response = MagicMock()
    mock_response.candidates = [MagicMock()]
    mock_response.candidates[0].content = MagicMock()
    mock_response.candidates[0].content.parts = [MagicMock(text="ls -la")]

    with patch("google.genai.Client") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.return_value = mock_client

        result = provider.get_bash_command("list files")

        assert result == "ls -la"
        mock_client.models.generate_content.assert_called_once_with(
            model="gemini-2.5-flash",
            contents="list files",
            config=GenerateContentConfig(
                max_output_tokens=150,
                temperature=0.0,
                system_instruction=SYSTEM_PROMPT,
            ),
        )


def test_get_bash_command_api_exception(mock_gemini_key):
    """Test get_bash_command with API exception."""
    config = {"model_name": "gemini-2.5-flash"}
    provider = GeminiProvider(config)

    with patch("google.genai.Client") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API error")
        mock_genai.return_value = mock_client

        # This should trigger the exception handling and return empty string
        with pytest.raises(APIError, match="API request failed"):
            provider.get_bash_command("test prompt")


def test_get_bash_command_auto_validate(mock_gemini_key):
    """Test auto-validation behavior."""
    config = {}
    provider = GeminiProvider(config)

    mock_response = MagicMock()
    mock_response.candidates = [MagicMock()]
    mock_response.candidates[0].content = MagicMock()
    mock_response.candidates[0].content.parts = [MagicMock(text="ls -la")]

    with patch("google.genai.Client") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.return_value = mock_client

        # Client should be None initially
        assert provider.client is None

        result = provider.get_bash_command("list files")

        # Client should be set after auto-validation
        assert provider.client is not None
        assert result == "ls -la"


def test_handle_api_error_auth():
    """Test authentication error mapping."""
    provider = GeminiProvider({})

    with pytest.raises(AuthenticationError, match="Invalid API key"):
        provider._handle_api_error(Exception("authentication failed"))


def test_handle_api_error_rate_limit():
    """Test rate limit error mapping."""
    provider = GeminiProvider({})

    with pytest.raises(RateLimitError, match="API rate limit exceeded"):
        provider._handle_api_error(Exception("rate limit exceeded"))


def test_handle_api_error_generic():
    """Test generic API error mapping."""
    provider = GeminiProvider({})

    with pytest.raises(APIError, match="API request failed"):
        provider._handle_api_error(Exception("unexpected error"))


def test_config_parameter_usage(mock_gemini_key):
    """Test configuration parameter usage."""
    config = {
        "model_name": "gemini-2.5-pro",
        "max_tokens": 1024,
        "temperature": 0.5,
        "system_prompt": "Custom system prompt",
    }
    provider = GeminiProvider(config)

    mock_response = MagicMock()
    mock_response.candidates = [MagicMock()]
    mock_response.candidates[0].content = MagicMock()
    mock_response.candidates[0].content.parts = [MagicMock(text="custom response")]

    with patch("google.genai.Client") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.return_value = mock_client

        result = provider.get_bash_command("test prompt")

        assert result == "custom response"
        mock_client.models.generate_content.assert_called_once_with(
            model="gemini-2.5-pro",
            contents="test prompt",
            config=GenerateContentConfig(
                max_output_tokens=1024,
                temperature=0.5,
                system_instruction="Custom system prompt",
            ),
        )
