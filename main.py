import argparse
import sys

import config
import providers
from exceptions import APIError, AuthenticationError, ConfigurationError


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="AI-powered bash command generator")
    parser.add_argument("prompt", help="Natural language description of the task")
    parser.add_argument(
        "--model", help="Provider and model to use (format: provider[:model])"
    )
    return parser.parse_args()


def load_configuration():
    """Load configuration from file and environment."""
    try:
        return config.load_config()
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)


def resolve_provider(args, config_data):
    """Determine which provider to use based on arguments and configuration."""
    if args.model:
        provider_name, provider_config = config.get_provider_config(
            config_data, args.model
        )
    else:
        # Check for default model in config first
        default_model = config.get_default_model(config_data)
        if default_model:
            provider_name, provider_config = config.get_provider_config(
                config_data, default_model
            )
        else:
            # Use default provider from environment variables
            default_provider = config.get_default_provider()
            if not default_provider:
                print(
                    "Error: No default model configured and no API keys found. "
                    "Please set ANTHROPIC_API_KEY or OPENAI_API_KEY environment"
                    " variable, or set a default_provider in your config file."
                )
                sys.exit(1)
            provider_name, provider_config = config.get_provider_config(
                config_data, default_provider
            )

    try:
        return providers.get_provider(provider_name, provider_config)
    except ConfigurationError as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    """Main entry point for the CLI application."""
    args = parse_arguments()
    config_data = load_configuration()

    try:
        provider = resolve_provider(args, config_data)
        provider.validate_config()
        bash_command = provider.get_bash_command(args.prompt)
        print(bash_command)
    except (AuthenticationError, APIError) as e:
        print(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
