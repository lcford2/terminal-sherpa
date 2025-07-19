"""Grok provider implementation using official xAI SDK."""

import os
import re
from typing import Any, NoReturn

from xai_sdk import Client
from xai_sdk.chat import system, user

from ask.config import SYSTEM_PROMPT
from ask.exceptions import APIError, AuthenticationError, RateLimitError
from ask.providers.base import ProviderInterface


class GrokProvider(ProviderInterface):
    """Grok provider implementation using official xAI SDK."""

    def __init__(self, config: dict[str, Any]):
        """Initialize Grok provider with configuration.

        Args:
            config: The configuration for the Grok provider
        """
        super().__init__(config)
        self.client: Client | None = None

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
            model_name = self.config.get("model_name", "grok-3-fast")
            system_prompt = self.config.get("system_prompt", SYSTEM_PROMPT)

            # Create chat using xAI SDK workflow
            chat = self.client.chat.create(model=model_name)
            chat.append(system(system_prompt))
            chat.append(user(prompt))

            # Get response
            response = chat.sample()
            content = response.content

            if content is None:
                raise APIError("Error: API returned empty response")

            # Remove ```bash and ``` from the content if present
            re_match = re.search(r"```bash\n(.*)\n```", content, re.DOTALL)
            if re_match is None:
                return content.strip()
            else:
                return re_match.group(1).strip()

        except Exception as e:
            self._handle_api_error(e)
            return ""

    def validate_config(self) -> None:
        """Validate provider configuration and API key."""
        api_key_env = self.config.get("api_key_env", "XAI_API_KEY")
        api_key = os.environ.get(api_key_env)

        if not api_key:
            raise AuthenticationError(
                f"Error: {api_key_env} environment variable is required"
            )

        # Initialize xAI SDK client
        self.client = Client(api_key=api_key)

    def _handle_api_error(self, error: Exception) -> NoReturn:
        """Handle API errors and map them to standard exceptions.

        Args:
            error: The exception to handle

        Raises:
            AuthenticationError: If the API key is invalid
            RateLimitError: If the API rate limit is exceeded
        """
        error_str = str(error).lower()

        if (
            "authentication" in error_str
            or "unauthorized" in error_str
            or "invalid api key" in error_str
        ):
            raise AuthenticationError("Error: Invalid API key")
        elif (
            "rate limit" in error_str
            or "quota" in error_str
            or "too many requests" in error_str
        ):
            raise RateLimitError("Error: API rate limit exceeded")
        else:
            raise APIError(f"Error: API request failed - {error}")

    @classmethod
    def get_default_config(cls) -> dict[str, Any]:
        """Return default configuration for Grok provider."""
        return {
            "model_name": "grok-3-fast",
            "max_tokens": 150,
            "api_key_env": "XAI_API_KEY",
            "temperature": 0.0,
            "system_prompt": SYSTEM_PROMPT,
        }
