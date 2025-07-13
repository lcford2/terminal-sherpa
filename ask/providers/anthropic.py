"""Anthropic provider implementation."""

import os
from typing import Any

import anthropic

from ask.config import SYSTEM_PROMPT
from ask.exceptions import APIError, AuthenticationError, RateLimitError
from ask.providers.base import ProviderInterface


class AnthropicProvider(ProviderInterface):
    """Anthropic AI provider implementation."""

    def __init__(self, config: dict[str, Any]):
        """Initialize Anthropic provider with configuration."""
        super().__init__(config)
        self.client: anthropic.Anthropic | None = None

    def get_bash_command(self, prompt: str) -> str:
        """Generate bash command from natural language prompt."""
        if self.client is None:
            self.validate_config()

        # After validate_config(), client should be set
        assert self.client is not None, "Client should be initialized after validation"

        try:
            response = self.client.messages.create(
                model=self.config.get("model_name", "claude-3-haiku-20240307"),
                max_tokens=self.config.get("max_tokens", 150),
                temperature=self.config.get("temperature", 0.0),
                system=self.config.get("system_prompt", SYSTEM_PROMPT),
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            self._handle_api_error(e)

    def validate_config(self) -> None:
        """Validate provider configuration and API key."""
        api_key_env = self.config.get("api_key_env", "ANTHROPIC_API_KEY")
        api_key = os.environ.get(api_key_env)

        if not api_key:
            raise AuthenticationError(
                f"Error: {api_key_env} environment variable is required"
            )

        self.client = anthropic.Anthropic(api_key=api_key)

    def _handle_api_error(self, error: Exception):
        """Handle API errors and map them to standard exceptions."""
        error_str = str(error).lower()

        if "authentication" in error_str or "unauthorized" in error_str:
            raise AuthenticationError("Error: Invalid API key")
        elif "rate limit" in error_str:
            raise RateLimitError("Error: API rate limit exceeded")
        else:
            raise APIError(f"Error: API request failed - {error}")

    @classmethod
    def get_default_config(cls) -> dict[str, Any]:
        """Return default configuration for Anthropic provider."""
        return {
            "model_name": "claude-3-haiku-20240307",
            "max_tokens": 150,
            "api_key_env": "ANTHROPIC_API_KEY",
            "temperature": 0.0,
            "system_prompt": SYSTEM_PROMPT,
        }
