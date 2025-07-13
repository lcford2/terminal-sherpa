"""Custom exception classes for the ask CLI tool."""


class ConfigurationError(Exception):
    """Raised when there are configuration-related errors."""

    pass


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass


class APIError(Exception):
    """Raised when API requests fail."""

    pass


class RateLimitError(APIError):
    """Raised when API rate limits are exceeded."""

    pass
