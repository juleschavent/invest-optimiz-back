"""
Exception Handlers for FastAPI

Converts custom exceptions into proper HTTP responses.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.exceptions import (
    AIServiceError,
    AppException,
    DatabaseError,
    NotFoundError,
    PDFProcessingError,
    ValidationError,
)
from app.logger import get_logger

logger = get_logger(__name__)


async def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all custom AppException errors.

    Returns a JSON response with error details.
    """
    # Type guard - this handler is only registered for AppException
    if not isinstance(exc, AppException):
        # Fallback to generic handler
        return await generic_exception_handler(request, exc)

    logger.error(
        f"{exc.__class__.__name__}: {exc.message}",
        extra={"details": exc.details, "path": request.url.path},
    )

    # Map exception types to HTTP status codes
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    if isinstance(exc, NotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, ValidationError):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, PDFProcessingError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, DatabaseError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    elif isinstance(exc, AIServiceError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions.

    Catches any exception that wasn't specifically handled.
    """
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={"path": request.url.path},
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "details": {},
        },
    )
