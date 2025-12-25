from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import event, text
from app.core.config import settings
from app.common.models import Base
from app.core.context import current_tenant_id

# Echo SQL only in debug mode (12-factor: environment-based config)
# PostgreSQL connection pool settings
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db() -> None:
    """Initialize database tables. Called on application startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def set_tenant_context(session, transaction, connection):
    """Event listener to set tenant context on new transactions."""
    tid = current_tenant_id.get()
    if tid is not None:
        # Validate tid type
        if not isinstance(tid, int):
            raise ValueError(f"tenant_id must be int, got {type(tid)}")
        # Using string interpolation for the setting name, but parameterized for value
        # Postgres SET LOCAL takes a string literal, parameter binding not work for SET command directly in some drivers
        # standard safe way:
        connection.execute(text(f"SET LOCAL app.current_tenant_id = '{tid}'"))


async def get_db():
    """Dependency for getting database sessions."""
    async with AsyncSessionLocal() as session:
        # Register event to set tenant_id when transaction begins
        event.listen(session.sync_session, "after_begin", set_tenant_context)
        try:
            yield session
        finally:
            # Not strictly necessary as session is closed, but good practice
            event.remove(session.sync_session, "after_begin", set_tenant_context)
