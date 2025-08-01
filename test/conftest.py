"""Pytest configuration and fixtures."""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def temp_config_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for config files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_resources_dir() -> Path:
    """Return path to test resources directory."""
    return Path(__file__).parent / "test_resources"


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {}, clear=True):
        yield


@pytest.fixture
def mock_anthropic_key():
    """Mock Anthropic API key in environment."""
    with patch.dict(
        os.environ, {"ANTHROPIC_API_KEY": "test-anthropic-key"}, clear=True
    ):
        yield


@pytest.fixture
def mock_gemini_key():
    """Mock Gemini API key in environment."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-gemini-key"}, clear=True):
        yield


@pytest.fixture
def mock_openai_key():
    """Mock OpenAI API key in environment."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-openai-key"}, clear=True):
        yield


@pytest.fixture
def mock_grok_key():
    """Mock Grok API key in environment."""
    with patch.dict(os.environ, {"XAI_API_KEY": "test-grok-key"}, clear=True):
        yield


@pytest.fixture
def mock_both_keys():
    """Mock both API keys in environment."""
    with patch.dict(
        os.environ,
        {
            "ANTHROPIC_API_KEY": "test-anthropic-key",
            "OPENAI_API_KEY": "test-openai-key",
        },
    ):
        yield


@pytest.fixture
def mock_ollama_server():
    """Mock Ollama server for testing."""
    with patch("ollama.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock successful list() call
        mock_client.list.return_value = {
            "models": [
                {"name": "llama3.2"},
                {"name": "codellama"},
            ]
        }

        yield mock_client
