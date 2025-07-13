"""OpenAI provider implementation (stub for future implementation)."""

from typing import Any

from .base import ProviderInterface


class OpenAIProvider(ProviderInterface):
    """OpenAI provider implementation (stub)."""

    def get_bash_command(self, prompt: str) -> str:
        """Generate bash command from natural language prompt."""
        raise NotImplementedError("OpenAI provider is not yet implemented")

    def validate_config(self) -> None:
        """Validate provider configuration and API key."""
        raise NotImplementedError("OpenAI provider is not yet implemented")

    @classmethod
    def get_default_config(cls) -> dict[str, Any]:
        """Return default configuration for OpenAI provider."""
        return {
            "model_name": "gpt-3.5-turbo",
            "max_tokens": 150,
            "api_key_env": "OPENAI_API_KEY",
            "system_prompt": (
                "You are a bash command generator. Given a user request, "
                "respond with ONLY the bash command that accomplishes the task. "
                "Do not include explanations, comments, or any other text. "
                "Just the command.",
            ),
        }
