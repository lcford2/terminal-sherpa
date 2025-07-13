import argparse
import sys
from typing import Any

from loguru import logger

import ask.config as config
import ask.providers as providers
from ask.exceptions import APIError, AuthenticationError, ConfigurationError
from ask.providers.base import ProviderInterface


def configure_logging(verbose: bool) -> None:
    """Configure loguru logging with appropriate level and format."""
    logger.remove()  # Remove default handler

    level = "DEBUG" if verbose else "ERROR"

    logger.add(
        sys.stderr,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | <level>{level}</level> | {message}",
        level=level,
        colorize=True,
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="AI-powered bash command generator")
    parser.add_argument("prompt", help="Natural language description of the task")
    parser.add_argument(
        "--model", help="Provider and model to use (format: provider[:model])"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    return parser.parse_args()


def load_configuration() -> dict[str, Any]:
    """Load configuration from file and environment."""
    try:
        return config.load_config()
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)


def resolve_provider(args, config_data) -> ProviderInterface:
    """Determine which provider to use based on arguments and configuration.

    Args:
        args: Parsed command line arguments
        config_data: Configuration data loaded from the config file

    Returns:
        Provider instance
    """
    if args.model:
        logger.debug(f"Using model specified via --model argument: {args.model}")
        provider_name, provider_config = config.get_provider_config(
            config_data, args.model
        )
    else:
        # Check for default model in config first
        default_model = config.get_default_model(config_data)
        if default_model:
            logger.debug(f"Using default model from config: {default_model}")
            provider_name, provider_config = config.get_provider_config(
                config_data, default_model
            )
        else:
            logger.warning(
                "No default model configured, falling back to environment variables"
            )
            # Use default provider from environment variables
            default_provider = config.get_default_provider()
            if not default_provider:
                logger.error(
                    "No default model configured and no API keys found. "
                    "Please set ANTHROPIC_API_KEY or OPENAI_API_KEY environment "
                    "variable, or set a default_provider in your config file."
                )
                sys.exit(1)
            logger.debug(f"Using default provider from environment: {default_provider}")
            provider_name, provider_config = config.get_provider_config(
                config_data, default_provider
            )

    try:
        logger.debug(f"Initializing provider: {provider_name}")
        return providers.get_provider(provider_name, provider_config)
    except ConfigurationError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI application."""
    args = parse_arguments()
    configure_logging(args.verbose)
    config_data = load_configuration()

    try:
        provider = resolve_provider(args, config_data)
        provider.validate_config()
        bash_command = provider.get_bash_command(args.prompt)
        print(bash_command)
    except (AuthenticationError, APIError) as e:
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
