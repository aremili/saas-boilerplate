from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info(f"Starting {settings.PROJECT_NAME}...")
    # Startup: Initialize database
    await init_db()
    logger.info("Database initialized")

    # Sync RBAC permissions and roles
    async with AsyncSessionLocal() as session:
        await sync_rbac(session)

    yield

    # Shutdown: cleanup to add?
    logger.info("Shutting down...")


app: FastAPI = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# Register exception handlers
register_exception_handlers(app)

# Add middleware
app.add_middleware(TenantContextMiddleware)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Common routers
app.include_router(home.router)
app.include_router(auth_router)
app.include_router(admin_router)

# Modules routers
app.include_router(task_router)


from app.core.database import get_db

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        # Check database connectivity
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable"
        )
