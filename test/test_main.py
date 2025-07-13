"""Tests for the CLI interface."""

import argparse
from unittest.mock import MagicMock, patch

import pytest

from ask.exceptions import APIError, AuthenticationError, ConfigurationError
from ask.main import (
    configure_logging,
    load_configuration,
    main,
    parse_arguments,
    resolve_provider,
)


def test_parse_arguments_basic():
    """Test basic argument parsing."""
    with patch("sys.argv", ["ask", "list files"]):
        args = parse_arguments()
        assert args.prompt == "list files"
        assert args.model is None
        assert args.verbose is False


def test_parse_arguments_with_model():
    """Test --model argument."""
    with patch("sys.argv", ["ask", "list files", "--model", "anthropic:sonnet"]):
        args = parse_arguments()
        assert args.prompt == "list files"
        assert args.model == "anthropic:sonnet"


def test_parse_arguments_with_verbose():
    """Test --verbose flag."""
    with patch("sys.argv", ["ask", "list files", "--verbose"]):
        args = parse_arguments()
        assert args.prompt == "list files"
        assert args.verbose is True


def test_configure_logging_verbose():
    """Test verbose logging configuration."""
    with patch("ask.main.logger") as mock_logger:
        configure_logging(verbose=True)
        mock_logger.remove.assert_called_once()
        mock_logger.add.assert_called_once()

        # Check that DEBUG level was set
        call_args = mock_logger.add.call_args
        assert "DEBUG" in str(call_args)


def test_configure_logging_normal():
    """Test normal logging configuration."""
    with patch("ask.main.logger") as mock_logger:
        configure_logging(verbose=False)
        mock_logger.remove.assert_called_once()
        mock_logger.add.assert_called_once()

        # Check that ERROR level was set
        call_args = mock_logger.add.call_args
        assert "ERROR" in str(call_args)


def test_load_configuration_success():
    """Test successful config loading."""
    mock_config = {"ask": {"default_model": "anthropic"}}

    with patch("ask.config.load_config", return_value=mock_config):
        config = load_configuration()
        assert config == mock_config


def test_load_configuration_error():
    """Test configuration error handling."""
    with patch(
        "ask.config.load_config", side_effect=ConfigurationError("Config error")
    ):
        with patch("ask.main.logger") as mock_logger:
            with pytest.raises(SystemExit):
                load_configuration()
            mock_logger.error.assert_called_once_with(
                "Configuration error: Config error"
            )


def test_resolve_provider_with_model_arg():
    """Test provider resolution with --model."""
    args = argparse.Namespace(model="anthropic:sonnet")
    config_data = {}
    mock_provider = MagicMock()

    with patch("ask.config.get_provider_config", return_value=("anthropic", {})):
        with patch("ask.providers.get_provider", return_value=mock_provider):
            with patch("ask.main.logger"):
                result = resolve_provider(args, config_data)
                assert result == mock_provider


def test_resolve_provider_with_default_model():
    """Test default model from config."""
    args = argparse.Namespace(model=None)
    config_data = {"ask": {"default_model": "anthropic"}}
    mock_provider = MagicMock()

    with patch("ask.config.get_default_model", return_value="anthropic"):
        with patch("ask.config.get_provider_config", return_value=("anthropic", {})):
            with patch("ask.providers.get_provider", return_value=mock_provider):
                with patch("ask.main.logger"):
                    result = resolve_provider(args, config_data)
                    assert result == mock_provider


def test_resolve_provider_with_env_fallback():
    """Test environment variable fallback."""
    args = argparse.Namespace(model=None)
    config_data = {}
    mock_provider = MagicMock()

    with patch("ask.config.get_default_model", return_value=None):
        with patch("ask.config.get_default_provider", return_value="anthropic"):
            with patch(
                "ask.config.get_provider_config", return_value=("anthropic", {})
            ):
                with patch("ask.providers.get_provider", return_value=mock_provider):
                    with patch("ask.main.logger"):
                        result = resolve_provider(args, config_data)
                        assert result == mock_provider


def test_resolve_provider_no_keys():
    """Test when no API keys available."""
    args = argparse.Namespace(model=None)
    config_data = {}

    with patch("ask.config.get_default_model", return_value=None):
        with patch("ask.config.get_default_provider", return_value=None):
            with patch("ask.main.logger") as mock_logger:
                with pytest.raises(SystemExit):
                    resolve_provider(args, config_data)
                mock_logger.error.assert_called()


def test_main_success():
    """Test successful main function execution."""
    mock_provider = MagicMock()
    mock_provider.get_bash_command.return_value = "ls -la"

    with patch("ask.main.parse_arguments") as mock_parse:
        with patch("ask.main.configure_logging"):
            with patch("ask.main.load_configuration", return_value={}):
                with patch("ask.main.resolve_provider", return_value=mock_provider):
                    with patch("builtins.print") as mock_print:
                        mock_parse.return_value = argparse.Namespace(
                            prompt="list files", model=None, verbose=False
                        )

                        main()

                        mock_provider.validate_config.assert_called_once()
                        mock_provider.get_bash_command.assert_called_once_with(
                            "list files"
                        )
                        mock_print.assert_called_once_with("ls -la")


def test_main_authentication_error():
    """Test authentication error handling."""
    mock_provider = MagicMock()
    mock_provider.validate_config.side_effect = AuthenticationError("Invalid API key")

    with patch("ask.main.parse_arguments") as mock_parse:
        with patch("ask.main.configure_logging"):
            with patch("ask.main.load_configuration", return_value={}):
                with patch("ask.main.resolve_provider", return_value=mock_provider):
                    with patch("ask.main.logger") as mock_logger:
                        mock_parse.return_value = argparse.Namespace(
                            prompt="list files", model=None, verbose=False
                        )

                        with pytest.raises(SystemExit):
                            main()

                        mock_logger.error.assert_called_once_with("Invalid API key")


def test_main_api_error():
    """Test API error handling."""
    mock_provider = MagicMock()
    mock_provider.get_bash_command.side_effect = APIError("API request failed")

    with patch("ask.main.parse_arguments") as mock_parse:
        with patch("ask.main.configure_logging"):
            with patch("ask.main.load_configuration", return_value={}):
                with patch("ask.main.resolve_provider", return_value=mock_provider):
                    with patch("ask.main.logger") as mock_logger:
                        mock_parse.return_value = argparse.Namespace(
                            prompt="list files", model=None, verbose=False
                        )

                        with pytest.raises(SystemExit):
                            main()

                        mock_logger.error.assert_called_once_with("API request failed")
