"""
Custom Exception Types for the Core Module.

This module defines a set of custom exceptions to be used throughout the
core application logic. Using custom exceptions allows for more specific
error handling and a clearer separation of concerns between the core logic
and the presentation layer (CLI, Bot).
"""

class CoreError(Exception):
    """Base class for all exceptions in the core module."""
    pass

class ConfigError(CoreError):
    """
    Raised for errors related to configuration, such as loading,
    saving, or validation issues.
    """
    pass

class APIError(CoreError):
    """
    Raised when there is an error communicating with the Cloudflare API.
    This serves as a wrapper around exceptions from the `cloudflare` library.
    """
    def __init__(self, message, original_exception=None):
        super().__init__(message)
        self.original_exception = original_exception

class InvalidInputError(CoreError):
    """
    Raised when a function in the core module receives invalid input,
    such as a malformed domain name or an invalid record type.
    """
    pass

class AuthenticationError(APIError):
    """
    Raised specifically for authentication failures with the Cloudflare API,
    such as an invalid or expired token.
    """
    pass