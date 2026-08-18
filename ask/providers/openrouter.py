"""OpenRouter provider implementation using the OpenAI-compatible API."""

import json
import os
from typing import Any, NoReturn

import openai

from ask.config import SYSTEM_PROMPT
from ask.exceptions import APIError, AuthenticationError, RateLimitError
from ask.providers.base import ProviderInterface

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

BASH_COMMAND_TOOL = {
    "type": "function",
    "function": {
        "name": "run_bash_command",
        "description": (
            "Return the bash command that accomplishes the user's request. "
            "Provide only the raw command, with no markdown formatting, "
            "backticks, or explanation."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to run.",
                },
            },
            "required": ["command"],
            "additionalProperties": False,
        },
    },
}

BASH_COMMAND_TOOL_CHOICE = {
    "type": "function",
    "function": {"name": "run_bash_command"},
}


class OpenRouterProvider(ProviderInterface):
    """OpenRouter provider implementation using the OpenAI-compatible API."""

    def __init__(self, config: dict[str, Any]):
        """Initialize OpenRouter provider with configuration.

        Args:
            config: The configuration for the OpenRouter provider
        """
        super().__init__(config)
        self.client: openai.OpenAI | None = None  # pragma: no mutate

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
                model=self.config.get("model_name", "openrouter/auto"),
                max_completion_tokens=self.config.get("max_tokens", 150),
                temperature=self.config.get("temperature", 0.5),
                messages=[
                    {
                        "role": "system",
                        "content": self.config.get("system_prompt", SYSTEM_PROMPT),
                    },
                    {"role": "user", "content": prompt},
                ],
                tools=[BASH_COMMAND_TOOL],
                tool_choice=BASH_COMMAND_TOOL_CHOICE,
            )
            tool_calls = response.choices[0].message.tool_calls
            if not tool_calls:
                raise APIError("Error: API returned empty response")

            try:
                arguments = json.loads(tool_calls[0].function.arguments)
            except json.JSONDecodeError as e:
                raise APIError(f"Error: API returned invalid JSON - {e}")

            command = arguments.get("command")
            if not command:
                raise APIError("Error: API returned empty response")

            return command.strip()
        except Exception as e:
            self._handle_api_error(e)

    def validate_config(self) -> None:
        """Validate provider configuration and API key."""
        api_key_env = self.config.get("api_key_env", "OPENROUTER_API_KEY")
        api_key = os.environ.get(api_key_env)

        if not api_key:
            raise AuthenticationError(
                f"Error: {api_key_env} environment variable is required"
            )

        base_url = self.config.get("base_url", OPENROUTER_BASE_URL)
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)

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
        """Return default configuration for OpenRouter provider."""
        return {
            "model_name": "openrouter/auto",
            "max_tokens": 150,
            "api_key_env": "OPENROUTER_API_KEY",
            "base_url": OPENROUTER_BASE_URL,
            "temperature": 0.5,
            "system_prompt": SYSTEM_PROMPT,
        }
