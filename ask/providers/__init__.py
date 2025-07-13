"""Provider registry and initialization module."""

from .anthropic import AnthropicProvider
from .base import ProviderInterface
from .openai import OpenAIProvider

# Provider registry - maps provider names to their classes
_PROVIDER_REGISTRY: dict[str, type[ProviderInterface]] = {}


def register_provider(name: str, provider_class: type[ProviderInterface]) -> None:
    """Register a provider class with the given name."""
    _PROVIDER_REGISTRY[name] = provider_class


def get_provider(name: str, config: dict) -> ProviderInterface:
    """Get a provider instance by name."""
    if name not in _PROVIDER_REGISTRY:
        from ask.exceptions import ConfigurationError

        raise ConfigurationError(
            f"Provider '{name}' not found. Available providers: {list_providers()}"
        )

    provider_class = _PROVIDER_REGISTRY[name]
    return provider_class(config)


def list_providers() -> list[str]:
    """List all available provider names."""
    return list(_PROVIDER_REGISTRY.keys())


register_provider("anthropic", AnthropicProvider)
register_provider("openai", OpenAIProvider)
