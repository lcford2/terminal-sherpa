"""OpenAI provider implementation."""

import os
import re
from typing import Any, NoReturn

import openai

from ask.config import SYSTEM_PROMPT
from ask.exceptions import APIError, AuthenticationError, RateLimitError
from ask.providers.base import ProviderInterface


class OpenAIProvider(ProviderInterface):
    """OpenAI provider implementation."""

    def __init__(self, config: dict[str, Any]):
        """Initialize OpenAI provider with configuration.

        Args:
            config: The configuration for the OpenAI provider
        """
        super().__init__(config)
        self.client: openai.OpenAI | None = None

    def get_bash_command(self, prompt: str) -> str:
        """Generate bash command from natural language prompt.

        Args:
            prompt: The natural language prompt to generate a bash command for

        Returns:
            The generated bash command
        """
        if self.client is None:
            self.validate_config()

        # After validate_config(), client should be set
        assert self.client is not None, "Client should be initialized after validation"

        try:
            response = self.client.chat.completions.create(
                model=self.config.get("model_name", "gpt-4o-mini"),
                max_completion_tokens=self.config.get("max_tokens", 150),
                temperature=self.config.get("temperature", 0.0),
                messages=[
                    {
                        "role": "system",
                        "content": self.config.get("system_prompt", SYSTEM_PROMPT),
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            content = response.choices[0].message.content
            if content is None:
                raise APIError("Error: API returned empty response")
            # Remove ```bash and ``` from the content
            re_match = re.search(r"```bash\n(.*)\n```", content)
            if re_match is None:
                return content
            else:
                return re_match.group(1)
        except Exception as e:
            self._handle_api_error(e)

    def validate_config(self) -> None:
        """Validate provider configuration and API key."""
        api_key_env = self.config.get("api_key_env", "OPENAI_API_KEY")
        api_key = os.environ.get(api_key_env)

        if not api_key:
            raise AuthenticationError(
                f"Error: {api_key_env} environment variable is required"
            )

        self.client = openai.OpenAI(api_key=api_key)

    def _handle_api_error(self, error: Exception) -> NoReturn:
        """Handle API errors and map them to standard exceptions.

        Args:
            error: The exception to handle

        Raises:
            AuthenticationError: If the API key is invalid
            RateLimitError: If the API rate limit is exceeded
        """
        error_str = str(error).lower()

        if "authentication" in error_str or "unauthorized" in error_str:
            raise AuthenticationError("Error: Invalid API key")
        elif "rate limit" in error_str or "quota" in error_str:
            raise RateLimitError("Error: API rate limit exceeded")
        else:
            raise APIError(f"Error: API request failed - {error}")

    @classmethod
    def get_default_config(cls) -> dict[str, Any]:
        """Return default configuration for OpenAI provider."""
        return {
            "model_name": "gpt-4o-mini",
            "max_tokens": 150,
            "api_key_env": "OPENAI_API_KEY",
            "temperature": 0.0,
            "system_prompt": SYSTEM_PROMPT,
        }
