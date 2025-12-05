"""
Custom exceptions and global exception handlers for FastAPI.

Provides:
- Custom exception hierarchy for application-specific errors
- Global exception handlers for clean error responses
- Proper error logging for all exceptions
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import get_logger

logger = get_logger(__name__)


# --- Custom Exception Hierarchy ---

class AppException(Exception):
    """Base exception for application errors."""
    
    def __init__(
        self,
        message: str = "An error occurred",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str | None = None
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail or message
        super().__init__(self.message)


class NotFoundException(AppException):
    """Resource not found exception."""
    
    def __init__(self, resource: str = "Resource", resource_id: int | str | None = None):
        message = f"{resource} not found"
        if resource_id is not None:
            message = f"{resource} with id '{resource_id}' not found"
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )


class ValidationException(AppException):
    """Business logic validation exception."""
    
    def __init__(self, message: str = "Validation failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class DatabaseException(AppException):
    """Database operation exception."""
    
    def __init__(self, message: str = "Database operation failed", original: Exception | None = None):
        self.original = original
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# --- Exception Handlers ---

def is_htmx_request(request: Request) -> bool:
    """Check if request is from HTMX."""
    return request.headers.get("HX-Request") == "true"


async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions."""
    logger.warning(f"AppException: {exc.message}", extra={"status_code": exc.status_code})
    
    if is_htmx_request(request):
        return HTMLResponse(
            content=f'<div class="error-message">{exc.message}</div>',
            status_code=exc.status_code
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "detail": exc.detail}
    )


async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle SQLAlchemy database exceptions."""
    logger.error(f"Database error: {exc}", exc_info=True)
    
    if is_htmx_request(request):
        return HTMLResponse(
            content='<div class="error-message">A database error occurred. Please try again.</div>',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Database error", "detail": "A database error occurred"}
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle any unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    if is_htmx_request(request):
        return HTMLResponse(
            content='<div class="error-message">An unexpected error occurred. Please try again.</div>',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "detail": "An unexpected error occurred"}
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
