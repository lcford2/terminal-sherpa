"""Anthropic provider implementation."""

import os
from typing import Any

from google import genai
from google.genai.types import GenerateContentConfig, GenerateContentResponse

from ask.config import SYSTEM_PROMPT
from ask.exceptions import APIError, AuthenticationError, RateLimitError
from ask.providers.base import ProviderInterface


class GeminiProvider(ProviderInterface):
    """Gemini AI provider implementation."""

    def __init__(self, config: dict[str, Any]):
        """Initialize Gemini provider with configuration."""
        super().__init__(config)
        self.client: genai.Client | None = None

    def _parse_response(self, response: GenerateContentResponse) -> str:
        """Parse response from Gemini API."""
        if response.candidates is None or len(response.candidates) == 0:
            return ""
        parts = response.candidates[0].content.parts
        if parts is None:
            return ""
        return "".join([part.text for part in parts])

    def get_bash_command(self, prompt: str) -> str:
        """Generate bash command from natural language prompt."""
        if self.client is None:
            self.validate_config()

        # After validate_config(), client should be set
        assert self.client is not None, "Client should be initialized after validation"

        try:
            # max_tokens=self.config.get("max_tokens", 150),
            # temperature=self.config.get("temperature", 0.0),
            # system=self.config.get("system_prompt", SYSTEM_PROMPT),
            response = self.client.models.generate_content(
                model=self.config.get("model_name", "gemini-2.5-flash"),
                contents=prompt,
                config=GenerateContentConfig(
                    max_output_tokens=self.config.get("max_tokens", 150),
                    temperature=self.config.get("temperature", 0.0),
                    system_instruction=self.config.get("system_prompt", SYSTEM_PROMPT),
                ),
            )
            return self._parse_response(response)
        except Exception as e:
            self._handle_api_error(e)
            return ""

    def validate_config(self) -> None:
        """Validate provider configuration and API key."""
        api_key_env = self.config.get("api_key_env", "GEMINI_API_KEY")
        api_key = os.environ.get(api_key_env)

        if not api_key:
            raise AuthenticationError(
                f"Error: {api_key_env} environment variable is required"
            )

        self.client = genai.Client(api_key=api_key)

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
        """Return default configuration for Gemini provider."""
        return {
            "model_name": "gemini-2.5-flash",
            "max_tokens": 150,
            "api_key_env": "GEMINI_API_KEY",
            "temperature": 0.0,
            "system_prompt": SYSTEM_PROMPT,
        }
