"""Ollama provider implementation."""

from typing import Any

import ollama
from loguru import logger

from ask.config import SYSTEM_PROMPT
from ask.exceptions import APIError, AuthenticationError
from ask.providers.base import ProviderInterface

module_logger = logger.bind(module=__name__)


class OllamaProvider(ProviderInterface):
    """Ollama provider implementation for local models."""

    def __init__(self, config: dict[str, Any]):
        """Initialize Ollama provider with configuration."""
        super().__init__(config)
        self.client: ollama.Client | None = None

    def get_bash_command(self, prompt: str) -> str:
        """Generate bash command from natural language prompt."""
        if self.client is None:
            self.validate_config()

        # After validate_config(), client should be set
        if self.client is None:
            module_logger.error("Client should be initialized after validation")
            raise AssertionError("Client should be initialized after validation")

        model_name = self.config.get("model_name", "llama3.2")

        # Check if model is available
        try:
            models = self.client.list()
            available_models = [model.model for model in models.get("models", [])]
            # If model name is not a full model name, allow ollama to decide which
            # version to use if there are multiple available
            if ":" not in model_name:
                available_models = [model.split(":")[0] for model in available_models]
            module_logger.debug(f"Available models: {available_models}")
            if model_name not in available_models:
                raise APIError(
                    f"Model '{model_name}' not found. Run: ollama pull {model_name}"
                )
        except Exception as e:
            if "not found" in str(e).lower():
                raise APIError(
                    f"Model '{model_name}' not found. Run: ollama pull {model_name}"
                )
            self._handle_api_error(e)

        try:
            response = self.client.generate(
                model=model_name,
                prompt=prompt,
                system=self.config.get("system_prompt", SYSTEM_PROMPT),
                options={
                    "temperature": self.config.get("temperature", 0.5),
                    "num_predict": self.config.get("max_tokens", 150),
                },
            )
            response_text = response.response
            if response_text is None:
                raise APIError("Error: API returned empty response")
            return response_text

        except Exception as e:
            self._handle_api_error(e)

    def validate_config(self) -> None:
        """Validate provider configuration and connection."""
        host = self.config.get("host", "localhost")
        port = self.config.get("port", 11434)

        try:
            self.client = ollama.Client(host=f"http://{host}:{port}")
            # Test connection by listing models
            self.client.list()
        except Exception:
            raise AuthenticationError(
                f"Ollama server not running at {host}:{port}. Start with: ollama serve"
            )

    def _handle_api_error(self, error: Exception):
        """Handle API errors and map them to standard exceptions."""
        error_str = str(error).lower()

        if "connection" in error_str or "refused" in error_str:
            raise AuthenticationError("Error: Cannot connect to Ollama server")
        elif "not found" in error_str or "model" in error_str:
            raise APIError(f"Error: Model issue - {error}")
        else:
            raise APIError(f"Error: API request failed - {error}")

    @classmethod
    def get_default_config(cls) -> dict[str, Any]:
        """Return default configuration for Ollama provider."""
        return {
            "model_name": "llama3.2",
            "host": "localhost",
            "port": 11434,
            "system_prompt": SYSTEM_PROMPT,
            "temperature": 0.5,
            "max_tokens": 150,
        }
