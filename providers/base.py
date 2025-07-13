"""Abstract base class for all providers."""

from abc import ABC, abstractmethod

from config import Config


class ProviderInterface(ABC):
    """Abstract base class for all AI providers."""

    def __init__(self, config: Config):
        """Initialize provider with configuration."""
        self.config = config

    @abstractmethod
    def get_bash_command(self, prompt: str) -> str:
        """Generate bash command from natural language prompt."""
        pass

    @abstractmethod
    def validate_config(self) -> None:
        """Validate provider configuration and API key."""
        pass

    @classmethod
    @abstractmethod
    def get_default_config(cls) -> Config:
        """Return default configuration for this provider."""
        pass
