"""
Custom Exception Classes

Defines application-specific exceptions for better error handling.
"""

from typing import Any


class AppException(Exception):
    """
    Base exception for all application errors.

    All custom exceptions should inherit from this.
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DatabaseError(AppException):
    """
    Raised when database operations fail.

    Examples:
    - Connection failures
    - Query errors
    - Constraint violations
    """

    pass


class ValidationError(AppException):
    """
    Raised when input validation fails.

    Examples:
    - Invalid file format
    - Missing required fields
    - Data out of range
    """

    pass


class NotFoundError(AppException):
    """
    Raised when a requested resource doesn't exist.

    Examples:
    - Statement not found
    - Analysis not found
    """

    pass


class CSVProcessingError(AppException):
    """
    Raised when CSV parsing fails.

    Examples:
    - Invalid CSV format
    - Missing required columns
    - Corrupted file
    - Empty file
    """

    pass


class AIServiceError(AppException):
    """
    Raised when Claude API calls fail.

    Examples:
    - API key invalid
    - Rate limit exceeded
    - Network errors
    """

    pass
