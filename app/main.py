"""FastAPI application factory."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal, get_db
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import register_exception_handlers
from app.core.middleware import TenantContextMiddleware
from app.routers.web import home
from app.modules.task import router as task_router
from app.common.auth import router as auth_router
from app.common.admin import router as admin_router

# Import permissions and roles to register them
import app.common.auth.permissions  # noqa: F401
import app.common.auth.default_roles  # noqa: F401
import app.modules.task.permissions  # noqa: F401

from app.common.auth.rbac_sync import sync_rbac

# Initialize logging
setup_logging()
logger = get_logger(__name__)


def create_app(
    init_database: bool = True,
    include_static: bool = True,
) -> FastAPI:
    """
    Create and configure the FastAPI application.

    Args:
        init_database: Initialize database on startup (disable for tests)
        include_static: Mount static files (disable for tests)
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan events"""
        if init_database:
            logger.info(f"Starting {settings.PROJECT_NAME}...")
            await init_db()
            logger.info("Database initialized")

            async with AsyncSessionLocal() as session:
                await sync_rbac(session)

        yield

        if init_database:
            logger.info("Shutting down...")

    application = FastAPI(
        title=settings.PROJECT_NAME, lifespan=lifespan, docs_url=None, redoc_url=None
    )

    # Register exception handlers
    register_exception_handlers(application)

    # Add middleware
    application.add_middleware(TenantContextMiddleware)

    # Mount static files
    if include_static:
        application.mount("/static", StaticFiles(directory="app/static"), name="static")

    # Common routers
    application.include_router(home.router)
    application.include_router(auth_router)
    application.include_router(admin_router)

    # Modules routers
    application.include_router(task_router)

    # Health check endpoint
    @application.get("/health")
    async def health_check(db: AsyncSession = Depends(get_db)):
        try:
            await db.execute(text("SELECT 1"))
            return {"status": "ok", "database": "connected"}
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable",
            )

    return application


# Default app instance for production
app: FastAPI = create_app()
