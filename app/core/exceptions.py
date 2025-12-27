"""Custom exceptions and exception handlers."""

from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import get_logger

logger = get_logger(__name__)


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        message: str = "An error occurred",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(AppException):
    """Resource not found."""

    def __init__(
        self, resource: str = "Resource", resource_id: str | int | None = None
    ):
        message = f"{resource} not found"
        if resource_id is not None:
            message = f"{resource} with id '{resource_id}' not found"
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)


class ValidationError(AppException):
    """Validation error."""

    def __init__(self, message: str = "Validation failed"):
        super().__init__(
            message=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


async def handle_app_exception(request: Request, exc: AppException):
    """Handle AppException with HTML response."""
    logger.warning(f"{exc.__class__.__name__}: {exc.message}")
    return HTMLResponse(
        content=f'<div class="error-message">{exc.message}</div>',
        status_code=exc.status_code,
    )


async def handle_database_error(request: Request, exc: SQLAlchemyError):
    """Handle database errors."""
    logger.error(f"Database error: {exc}", exc_info=True)
    return HTMLResponse(
        content='<div class="error-message">A database error occurred.</div>',
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def handle_http_exception(request: Request, exc):
    """Handle HTTPException with HTML error pages."""
    from fastapi.responses import RedirectResponse
    from app.core.templates import templates

    # Redirects pass through
    if 300 <= exc.status_code < 400:
        return RedirectResponse(
            url=exc.headers.get("Location", "/"),
            status_code=exc.status_code,
        )

    # 403 Forbidden - render error page
    if exc.status_code == 403:
        return templates.TemplateResponse(
            "errors/403.html",
            {"request": request, "detail": exc.detail},
            status_code=403,
        )

    # Default HTML error
    return HTMLResponse(
        content=f'<div class="error-message">{exc.detail}</div>',
        status_code=exc.status_code,
    )


async def handle_unhandled_exception(request: Request, exc: Exception):
    """Handle unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return HTMLResponse(
        content='<div class="error-message">An unexpected error occurred.</div>',
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers with the FastAPI app."""
    from fastapi import HTTPException

    app.add_exception_handler(AppException, handle_app_exception)
    app.add_exception_handler(SQLAlchemyError, handle_database_error)
    app.add_exception_handler(HTTPException, handle_http_exception)
    app.add_exception_handler(Exception, handle_unhandled_exception)
