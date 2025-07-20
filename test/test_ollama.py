"""Tests for Ollama provider."""

from unittest.mock import ANY, MagicMock, patch

import pytest

from ask.config import SYSTEM_PROMPT
from ask.exceptions import APIError, AuthenticationError
from ask.providers.ollama import OllamaProvider


def test_ollama_provider_init():
    """Test provider initialization."""
    config = {"model_name": "llama3.2", "host": "localhost", "port": 11434}
    provider = OllamaProvider(config)

    assert provider.config == config
    assert provider.client is None


def test_validate_config_success(mock_ollama_server):
    """Test successful config validation."""
    config = {"host": "localhost", "port": 11434}
    provider = OllamaProvider(config)

    with patch("ollama.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.list.return_value = {"models": []}

        provider.validate_config()

        assert provider.client == mock_client
        mock_client_class.assert_called_once_with(host="http://localhost:11434")
        mock_client.list.assert_called_once()


def test_validate_config_server_not_running():
    """Test server not running error."""
    config = {"host": "localhost", "port": 11434}
    provider = OllamaProvider(config)

    with patch("ollama.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.list.side_effect = Exception("Connection refused")

        with pytest.raises(
            AuthenticationError,
            match=(
                "Ollama server not running at localhost:11434. "
                "Start with: ollama serve"
            ),
        ):
            provider.validate_config()


def test_validate_config_custom_host_port():
    """Test custom host and port configuration."""
    config = {"host": "remote-host", "port": 8080}
    provider = OllamaProvider(config)

    with patch("ollama.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.list.return_value = {"models": []}

        provider.validate_config()

        mock_client_class.assert_called_once_with(host="http://remote-host:8080")


def test_get_default_config():
    """Test default configuration values."""
    default_config = OllamaProvider.get_default_config()

    assert default_config["model_name"] == "llama3.2"
    assert default_config["host"] == "localhost"
    assert default_config["port"] == 11434
    assert default_config["system_prompt"] == SYSTEM_PROMPT


def test_get_bash_command_success(mock_ollama_server):
    """Test successful command generation."""
    config = {"model_name": "llama3.2"}
    provider = OllamaProvider(config)

    mock_response = MagicMock()
    mock_response.response = "ls -la"

    with patch("ollama.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_model = MagicMock()
        mock_model.model = "llama3.2"
        mock_client.list.return_value = {"models": [mock_model]}
        mock_client.generate.return_value = mock_response

        result = provider.get_bash_command("list files")

        assert result == "ls -la"
        mock_client.generate.assert_called_once_with(
            model="llama3.2",
            prompt="list files",
            system=ANY,
            options=ANY,
        )


def test_get_bash_command_model_not_found():
    """Test model not found error."""
    config = {"model_name": "nonexistent-model"}
    provider = OllamaProvider(config)

    with patch("ollama.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_model = MagicMock()
        mock_model.model = "llama3.2"
        mock_client.list.return_value = {"models": [mock_model]}

        with pytest.raises(
            APIError,
            match=(
                "Model 'nonexistent-model' not found. "
                "Run: ollama pull nonexistent-model"
            ),
        ):
            provider.get_bash_command("test prompt")


def test_get_bash_command_auto_validate():
    """Test auto-validation behavior."""
    config = {}
    provider = OllamaProvider(config)

    mock_response = MagicMock()
    mock_response.response = "ls -la"

    with patch("ollama.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_model = MagicMock()
        mock_model.model = "llama3.2"
        mock_client.list.return_value = {"models": [mock_model]}
        mock_client.generate.return_value = mock_response

        # Client should be None initially
        assert provider.client is None

        result = provider.get_bash_command("list files")

        # Client should be set after auto-validation
        assert provider.client is not None
        assert result == "ls -la"


def test_handle_api_error_connection():
    """Test connection error mapping."""
    provider = OllamaProvider({})

    with pytest.raises(AuthenticationError, match="Cannot connect to Ollama server"):
        provider._handle_api_error(Exception("connection refused"))


def test_handle_api_error_model_not_found():
    """Test model not found error mapping."""
    provider = OllamaProvider({})

    with pytest.raises(APIError, match="Model issue"):
        provider._handle_api_error(Exception("model not found"))


def test_handle_api_error_generic():
    """Test generic API error mapping."""
    provider = OllamaProvider({})

    with pytest.raises(APIError, match="API request failed"):
        provider._handle_api_error(Exception("unexpected error"))


def test_config_parameter_usage():
    """Test configuration parameter usage."""
    config = {
        "model_name": "codellama",
        "host": "custom-host",
        "port": 9999,
    }
    provider = OllamaProvider(config)

    mock_response = MagicMock()
    mock_response.response = "custom response"

    with patch("ollama.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_model = MagicMock()
        mock_model.model = "codellama"
        mock_client.list.return_value = {"models": [mock_model]}
        mock_client.generate.return_value = mock_response

        result = provider.get_bash_command("test prompt")

        assert result == "custom response"
        mock_client_class.assert_called_once_with(host="http://custom-host:9999")
        mock_client.generate.assert_called_once_with(
            model="codellama",
            prompt="test prompt",
            system=ANY,
            options=ANY,
        )


def test_get_bash_command_client_assertion_error():
    """Test AssertionError when client is None after validate_config."""
    config = {}
    provider = OllamaProvider(config)

    # Mock validate_config to not set client
    with patch.object(provider, "validate_config") as mock_validate:
        mock_validate.return_value = None  # Don't set self.client

        with pytest.raises(
            AssertionError, match="Client should be initialized after validation"
        ):
            provider.get_bash_command("test prompt")


def test_get_bash_command_generic_exception_in_model_check():
    """Test generic exception handling in model availability check."""
    config = {"model_name": "test-model"}
    provider = OllamaProvider(config)

    # Set up a mock client to bypass validate_config
    mock_client = MagicMock()
    provider.client = mock_client  # Set client directly to avoid validate_config

    # Make the model availability check raise a generic exception
    mock_client.list.side_effect = Exception("Generic error without 'not found'")

    with pytest.raises(Exception):
        provider.get_bash_command("test prompt")

    # mock_handle_error.assert_called_once()
    mock_client.list.assert_called_once()


def test_get_bash_command_empty_response_content():
    """Test APIError when response content is None."""
    config = {"model_name": "llama3.2"}
    provider = OllamaProvider(config)

    with patch("ollama.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock successful model list
        mock_model = MagicMock()
        mock_model.model = "llama3.2"
        mock_client.list.return_value = {"models": [mock_model]}

        # Mock generate with None response
        mock_response = MagicMock()
        mock_response.response = None
        mock_client.generate.return_value = mock_response

        with pytest.raises(APIError, match="API returned empty response"):
            provider.get_bash_command("test prompt")


def test_get_bash_command_exception_during_generation():
    """Test exception handling during generate call."""
    config = {"model_name": "llama3.2"}
    provider = OllamaProvider(config)

    with patch("ollama.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock successful model list
        mock_model = MagicMock()
        mock_model.model = "llama3.2"
        mock_client.list.return_value = {"models": [mock_model]}

        # Mock generate to raise exception
        mock_client.generate.side_effect = Exception("Generation failed")

        with patch.object(provider, "_handle_api_error") as mock_handle_error:
            mock_handle_error.side_effect = APIError("Handled generation error")

            with pytest.raises(APIError):
                provider.get_bash_command("test prompt")

            mock_handle_error.assert_called_once()
