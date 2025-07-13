"""Tests for the provider registry."""

import pytest

from ask.exceptions import ConfigurationError
from ask.providers import get_provider, list_providers, register_provider
from ask.providers.base import ProviderInterface


class MockProvider(ProviderInterface):
    """Mock provider for testing."""

    def get_bash_command(self, prompt: str) -> str:
        return f"mock command for: {prompt}"

    def validate_config(self) -> None:
        pass

    @classmethod
    def get_default_config(cls) -> dict:
        return {"mock": "config"}


def test_register_provider():
    """Test provider registration."""
    # Clean up any existing registration
    from ask.providers import _PROVIDER_REGISTRY

    if "test_provider" in _PROVIDER_REGISTRY:
        del _PROVIDER_REGISTRY["test_provider"]

    register_provider("test_provider", MockProvider)

    assert "test_provider" in _PROVIDER_REGISTRY
    assert _PROVIDER_REGISTRY["test_provider"] == MockProvider


def test_get_provider_success():
    """Test successful provider retrieval."""
    register_provider("test_provider", MockProvider)

    provider = get_provider("test_provider", {"test": "config"})

    assert isinstance(provider, MockProvider)
    assert provider.config == {"test": "config"}


def test_get_provider_not_found():
    """Test unknown provider error."""
    with pytest.raises(
        ConfigurationError, match="Provider 'unknown_provider' not found"
    ):
        get_provider("unknown_provider", {})


def test_list_providers():
    """Test provider listing."""
    register_provider("test_provider", MockProvider)

    providers = list_providers()

    assert isinstance(providers, list)
    assert "anthropic" in providers
    assert "openai" in providers


def test_provider_registry_isolation():
    """Test registry isolation between tests."""
    from ask.providers import _PROVIDER_REGISTRY

    # Register a temporary provider
    register_provider("temp_provider", MockProvider)
    assert "temp_provider" in _PROVIDER_REGISTRY

    # Clean up
    del _PROVIDER_REGISTRY["temp_provider"]
    assert "temp_provider" not in _PROVIDER_REGISTRY
