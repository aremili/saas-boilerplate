from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import init_db
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import register_exception_handlers
from app.routers.web import home
from app.modules.task import router as task_router
from app.common.auth import router as auth_router

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
    yield
    # Shutdown: cleanup if needed
    logger.info("Shutting down...")


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# Register exception handlers
register_exception_handlers(app)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(home.router)
app.include_router(task_router)
app.include_router(auth_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
