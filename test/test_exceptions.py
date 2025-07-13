"""Tests for custom exception classes."""

from ask.exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    RateLimitError,
)


def test_configuration_error():
    """Test ConfigurationError creation."""
    error = ConfigurationError("Config problem")
    assert str(error) == "Config problem"
    assert isinstance(error, Exception)


def test_authentication_error():
    """Test AuthenticationError creation."""
    error = AuthenticationError("Auth failed")
    assert str(error) == "Auth failed"
    assert isinstance(error, Exception)


def test_api_error():
    """Test APIError creation."""
    error = APIError("API failed")
    assert str(error) == "API failed"
    assert isinstance(error, Exception)


def test_rate_limit_error():
    """Test RateLimitError inheritance."""
    error = RateLimitError("Rate limit exceeded")
    assert str(error) == "Rate limit exceeded"
    assert isinstance(error, APIError)
    assert isinstance(error, Exception)


def test_exception_hierarchy():
    """Test exception inheritance hierarchy."""
    # Test that RateLimitError is a subclass of APIError
    assert issubclass(RateLimitError, APIError)

    # Test that all exceptions are subclasses of Exception
    assert issubclass(ConfigurationError, Exception)
    assert issubclass(AuthenticationError, Exception)
    assert issubclass(APIError, Exception)
    assert issubclass(RateLimitError, Exception)

    # Test that custom exceptions are not subclasses of each other
    assert not issubclass(ConfigurationError, AuthenticationError)
    assert not issubclass(AuthenticationError, ConfigurationError)
    assert not issubclass(APIError, ConfigurationError)
    assert not issubclass(APIError, AuthenticationError)
